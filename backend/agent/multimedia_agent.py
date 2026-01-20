import os
import uuid
import logging
from google.cloud import storage
from google.adk.agents import Agent, SequentialAgent, LlmAgent
from services.spanner_service import SpannerService
from config import settings
from agent.memory_agent import memory_agent

logger = logging.getLogger(__name__)

# --- Tools ---

def upload_to_gcs(file_path: str) -> str:
    """
    Uploads a file from the local file system to Google Cloud Storage.
    Returns the public GCS URI (gs://...).
    """
    try:
        # Initial validation of the file path
        if not file_path or not isinstance(file_path, str):
            return "Error: Invalid file path provided."
            
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"
            
        bucket_name = settings.GCS_BUCKET_NAME
        # Ensure bucket name is set
        if not bucket_name:
             return "Error: GCS_BUCKET_NAME not set in config."
             
        client = storage.Client(project=settings.PROJECT_ID)
        bucket = client.bucket(bucket_name)
        
        # Check if bucket exists (optional check, assuming it exists for performance)
        if not bucket.exists():
             return f"Error: Bucket {bucket_name} does not exist."

        blob_name = f"media/{uuid.uuid4()}_{os.path.basename(file_path)}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(file_path)
        
        gcs_uri = f"gs://{bucket_name}/{blob_name}"
        logger.info(f"Uploaded file to {gcs_uri}")
        return gcs_uri
        
    except Exception as e:
        logger.error(f"Error uploading to GCS: {e}")
        return f"Error uploading to GCS: {e}"

def update_spanner_with_media(gcs_uri: str, description: str = "User uploaded media") -> str:
    """
    Updates the Spanner graph with a new Media node representing the uploaded file.
    """
    try:
        if not gcs_uri or not gcs_uri.startswith("gs://"):
            return "Error: Invalid GCS URI."
            
        service = SpannerService()
        
        node_id = str(uuid.uuid4())
        timestamp = "CURRENT_TIMESTAMP()" # Spanner SQL syntax
        
        # Insert a Node with Label 'Media'
        # The query uses Graph GQL syntax: INSERT (:Label properties)
        # Note: Depending on the schema, ensure 'Media' label exists or is allowed.
        # Assuming open schema or pre-defined Media label.
        
        query = f"INSERT (:Media {{id: '{node_id}', uri: '{gcs_uri}', description: '{description}', created_at: {timestamp}}})"
        
        service.execute_update(query)
        logger.info(f"Created Media node {node_id} in Spanner")
        return f"Successfully added Media node {node_id} with URI {gcs_uri} to Spanner."
        
    except Exception as e:
        logger.error(f"Error updating Spanner: {e}")
        return f"Error updating Spanner: {e}"

# --- Agents Definition ---

# 1. GCS Uploader Agent
# This agent takes the user input (which should contain the file path) and uploads it.
uploader_agent = LlmAgent(
    name="GcsUploaderAgent",
    model="gemini-2.5-flash",
    instruction="""You are a file upload assistant.
    Your task is to identify file paths in the user's message and upload them to Google Cloud Storage using the `upload_to_gcs` tool.
    
    The user message will contain text like "Attached file path: /path/to/file".
    
    1. Extract the file path.
    2. Call `upload_to_gcs(file_path)`.
    3. Output *only* the GCS URI returned by the tool. Do not add any conversational text.
    """,
    tools=[upload_to_gcs],
    output_key="gcs_uri"
)

# 2. Spanner Updater Agent
# This agent takes the GCS URI from the previous agent and updates the database.
spanner_agent = LlmAgent(
    name="SpannerUpdaterAgent",
    model="gemini-2.5-flash",
    instruction="""You are a database updater.
    Your task is to register the uploaded media in the Spanner graph.
    
    Input GCS URI: {gcs_uri}
    
    1. Call the `update_spanner_with_media` tool.
    2. Use the provided URI and a generic description like "User uploaded media".
    3. Output the result message from the tool.
    """,
    tools=[update_spanner_with_media],
    output_key="spanner_result"
)

# 3. Memory Agent
# Reusing the existing memory agent to save the session context.
# The SequentialAgent will run this agent last.
# Since memory_agent is designed to run in background (via callback) or as a tool user,
# we include it here to ensure the flow passes through it.
# We wrap it or use it directly.

# --- Sequential Agent ---
multimedia_agent = SequentialAgent(
    name="MultimediaSequentialAgent",
    sub_agents=[uploader_agent, spanner_agent, memory_agent],
    description="Handles media upload sequence: GCS Upload -> Spanner Update -> Memory Bank Save."
)
