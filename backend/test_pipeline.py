import os
import asyncio
import logging
from unittest.mock import MagicMock
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from agent.multimedia_agent import multimedia_agent
from config import settings
import uuid
from google.cloud import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure env vars are set for GenAI SDK
if settings.GOOGLE_API_KEY and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
if settings.PROJECT_ID and "GOOGLE_CLOUD_PROJECT" not in os.environ:
    os.environ["GOOGLE_CLOUD_PROJECT"] = settings.PROJECT_ID
if settings.LOCATION and "GOOGLE_CLOUD_LOCATION" not in os.environ:
    os.environ["GOOGLE_CLOUD_LOCATION"] = settings.LOCATION

from tools import extraction_tools

def setup_test_files():
    # Text
    if "test_pipeline.txt" not in os.listdir("."):
        with open("test_pipeline.txt", "w") as f:
            f.write("""URGENT BROADCAST
Survivor: Sarah (Medic)
Location: NE Quadrant, Forest Biome
Status: Injured but stable
Needs: Medical Supplies (Bandages), Water
Found: Abandoned Supply Cache with Canned Food
Skills: First Aid, Navigation
Timestamp: 2026-05-12 14:00
""")
    
    # Dummy Image (if not exists)
    if "test_pipeline.png" not in os.listdir("."):
        # Create a tiny 1x1 transparent PNG
        with open("test_pipeline.png", "wb") as f:
             f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')

    print("Test files checked/created.")

async def create_test_bucket():
    """Creates a new GCS bucket for testing."""
    bucket_name = f"test-bucket-{uuid.uuid4()}"
    print(f"Creating test bucket: {bucket_name}")
    
    try:
        # Use simple instantiation if PROJECT_ID is set in env/default
        # Otherwise use project from settings
        storage_client = storage.Client(project=settings.PROJECT_ID)
        bucket = storage_client.create_bucket(bucket_name, location="us-central1")
        print(f"Bucket {bucket.name} created.")
        return bucket_name
    except Exception as e:
        print(f"Failed to create bucket: {e}")
        return None

def mock_save_to_spanner(extraction_result, survivor_id=None):
    """Verbose mock that prints what would happen"""
    print("\n[DRY RUN] Spanner Service Received Data:")
    
    # Handle the structure passed by the tool wrapper
    result = extraction_result
    if isinstance(result, dict) and 'extraction_result' in result:
        result = result['extraction_result']
        
    print(f"  - Media URI: {result.media_uri}")
    print(f"  - Survivor ID: {survivor_id}")
    
    print(f"  - Entities to Create ({len(result.entities)}):")
    for e in result.entities:
        print(f"    * [{e.entity_type.value}] {e.name} (Props: {list(e.properties.keys())})")
        
    print(f"  - Relationships to Create ({len(result.relationships)}):")
    for r in result.relationships:
        print(f"    * {r.source_name} --[{r.relationship_type.value}]--> {r.target_name}")
        
    print(f"  - Broadcast Node: {result.broadcast_info.get('title', 'Untitled')}")
    print("[DRY RUN] Success - would have committed transaction.\n")
    
    return {
        'entities_created': len(result.entities), 
        'entities_found_existing': 0,
        'relationships_created': len(result.relationships), 
        'broadcast_id': 'mock-broadcast-id', 
        'errors': []
    }

async def run_single_test(file_name, session_service, user_id):
    file_path = os.path.abspath(file_name)
    print(f"\n>>> Testing with file: {file_name}")
    
    app_name = f"pipeline-test-{uuid.uuid4().hex[:6]}"
    runner = Runner(agent=multimedia_agent, app_name=app_name, session_service=session_service)
    session = await session_service.create_session(user_id=user_id, app_name=app_name)
    
    message_text = f"Process this field report: {file_path}"
    user_msg = Content(role="user", parts=[Part(text=message_text)])
    
    try:
        async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=user_msg):
            if hasattr(event, "text") and event.text:
                print(f"Agent Output: {event.text}")
    except Exception as e:
        logger.error(f"Pipeline failed for {file_name}: {e}")

async def run_test(dry_run=True):
    print(f"--- Starting Pipeline Verification (Dry Run: {dry_run}) ---")
    setup_test_files()
    
    # Create a new bucket
    new_bucket_name = await create_test_bucket()
    if not new_bucket_name:
        print("Skipping test due to bucket creation failure.")
        return

    # Override settings to use the new bucket
    print(f"Overriding settings.GCS_BUCKET_NAME to {new_bucket_name}")
    original_bucket_name = settings.GCS_BUCKET_NAME
    settings.GCS_BUCKET_NAME = new_bucket_name

    # IMPORTANT: Re-initialize the tools/services so they pick up the new bucket name!
    # The instances were created at import time with the old setting.
    extraction_tools.gcs_service = extraction_tools.GCSService()
    extraction_tools.text_extractor = extraction_tools.TextExtractor()
    extraction_tools.image_extractor = extraction_tools.ImageExtractor()
    extraction_tools.video_extractor = extraction_tools.VideoExtractor()

    if dry_run:
        print("[INFO] Dry Run enabled. Spanner writes will be mocked but LOGGED below.")
        # Patch the method on the service instance
        extraction_tools.spanner_service.save_extraction_result = mock_save_to_spanner
    
    session_service = InMemorySessionService()
    user_id = "tester"
    
    # Run Tests
    await run_single_test("test_pipeline.txt", session_service, user_id)
    # await run_single_test("test_pipeline.png", session_service, user_id)

if __name__ == "__main__":
    asyncio.run(run_test(dry_run=True))
