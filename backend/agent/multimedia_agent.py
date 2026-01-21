import logging
from google.adk.agents import Agent, SequentialAgent, LlmAgent
from tools.extraction_tools import (
    upload_media, extract_from_media, save_to_spanner, process_media_upload
)
from agent.memory_agent import memory_agent

logger = logging.getLogger(__name__)

# --- Option 2: Sequential Pipeline ---

upload_agent = LlmAgent(
    name="UploadAgent",
    model="gemini-2.5-flash",
    instruction="""Extract the file path from the user's message and upload it.

Use `upload_media(file_path, survivor_id)` to upload the file.
The survivor_id is optional - include it if the user mentions a specific survivor (e.g., "survivor Sarah" -> "Sarah").
If the user provides a path like "/path/to/file", use that.

Return the upload result with gcs_uri and media_type.""",
    tools=[upload_media],
    output_key="upload_result"
)

extraction_agent = LlmAgent(
    name="ExtractionAgent", 
    model="gemini-2.5-flash",
    instruction="""Extract information from the uploaded media.

Previous step result: {upload_result}

Use `extract_from_media(gcs_uri, media_type)` with the values from the upload result.
The gcs_uri is in upload_result['gcs_uri'] and media_type in upload_result['media_type'].

Return the extraction results including entities and relationships found.""",
    tools=[extract_from_media],
    output_key="extraction_result"
)

spanner_agent = LlmAgent(
    name="SpannerAgent",
    model="gemini-2.5-flash", 
    instruction="""Save the extracted information to the database.

Upload result: {upload_result}
Extraction result: {extraction_result}

Use `save_to_spanner(extraction_result, survivor_id)` to save to Spanner.
Pass the WHOLE `extraction_result` object/dict from the previous step.
Include survivor_id if it was provided in the upload step.

Return the save statistics.""",
    tools=[save_to_spanner],
    output_key="spanner_result"
)

summary_agent = LlmAgent(
    name="SummaryAgent",
    model="gemini-2.5-flash",
    instruction="""Provide a user-friendly summary of the media processing.

Upload: {upload_result}
Extraction: {extraction_result}
Database: {spanner_result}

Summarize:
1. What file was processed (name and type)
2. Key information extracted (survivors, skills, needs, resources found) - list names and counts
3. Relationships identified
4. What was saved to the database (broadcast ID, number of entities)
5. Any issues encountered

Be concise but informative.""",
    output_key="final_summary"
)

multimedia_agent = SequentialAgent(
    name="MultimediaExtractionPipeline",
    description="Process media uploads: Upload -> Extract -> Save -> Summarize",
    sub_agents=[upload_agent, extraction_agent, spanner_agent, summary_agent]
)
