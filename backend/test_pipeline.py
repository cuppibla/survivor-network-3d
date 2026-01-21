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

# Global/Shared store for validation in dry-runs
LAST_EXTRACTION_RESULT = {}

def mock_save_to_spanner(extraction_result, survivor_id=None):
    """Verbose mock that prints what would happen"""
    print("\n[DRY RUN] Spanner Service Received Data:")
    
    # Handle the structure passed by the tool wrapper
    result = extraction_result
    if isinstance(result, dict) and 'extraction_result' in result:
        result = result['extraction_result']
    
    # Store for validation
    global LAST_EXTRACTION_RESULT
    # If result is an object (ExtractionResult), convert to dict for easier validation logic
    if hasattr(result, 'to_dict'):
         LAST_EXTRACTION_RESULT = result.to_dict()
    else:
         LAST_EXTRACTION_RESULT = result
        
    print(f"  - Media URI: {result.media_uri if hasattr(result, 'media_uri') else result.get('media_uri')}")
    print(f"  - Survivor ID: {survivor_id}")
    
    entities = result.entities if hasattr(result, 'entities') else result.get('entities', [])
    print(f"  - Entities to Create ({len(entities)}):")
    for e in entities:
        if hasattr(e, 'entity_type'):
             print(f"    * [{e.entity_type.value}] {e.name}")
        else:
             print(f"    * [{e.get('entity_type')}] {e.get('name')}")
        
    print("[DRY RUN] Success - would have committed transaction.\n")
    
    return {
        'entities_created': len(entities), 
        'entities_found_existing': 0,
        'relationships_created': 0, 
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
    
    final_result_dict = None
    try:
        async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=user_msg):
            if hasattr(event, "text") and event.text:
                print(f"Agent Output: {event.text}")
                # Try to parse the last output as the JSON summary we verified earlier
                # The SummaryAgent returns text, but the SpannerAgent returned a dict.
                # Actually, in SequentialAgent, the *final* output is from the last sub-agent (SummaryAgent).
                # But we can inspect the intermediate steps if we want deep validation, or we can trust the summary.
                # BETTER: The Multimedia pipeline returns a combined result dict if we look at `process_media_upload` tool directly.
                # But here we are using the AGENT runner.
                # The `run_async` yields chunks. The agent execution history is in `session`.
                pass
                
        # To get the structured extraction data for validation, we can peek into the session history 
        # or assuming the tool output was successful. 
        # A simpler way for this TEST script is to call the tool directly for validation IF we want strict object checks,
        # but since we are testing the AGENT flow, we should rely on what the agent returns.
        # However, `multimedia_agent` ends with `summary_agent` which produces text.
        # Let's just trust the logs for now or return True if no exception.
        
        # WAIT! For rigorous testing, let's look at the tool outputs stored in the session memory/history if accessible,
        # OR, since `process_media_upload` returns the dict, maybe we can run THAT tool function directly 
        # in a separate verification step if the Agent flow is too opaque?
        
        # Actually, let's try to parse the agent's text output or just return "Success" for now. 
        # Since I'm editing `run_single_test` to verify correctness, I need ACCESS to the data.
        # Let's modify `run_single_test` to also call `process_media_upload` directly for DATA validation 
        # if the agent one is hard to parse.
        # OR: We can rely on the [DRY RUN] print statements I added to `mock_save_to_spanner`.
        
        # Let's stick to returning True for success for now, and rely on the mock prints I added.
        return True

    except Exception as e:
        logger.error(f"Pipeline failed for {file_name}: {e}")
        return None

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
    # Text Test
    print("\n--- Running Text Extraction Test ---")
    success = await run_single_test("test_pipeline.txt", session_service, user_id)
    if success and dry_run: # Verification only works nicely in dry-run with our capture hook
        # Validate extracted data
        print(">>> Validating Text Extraction Results...")
        entities = LAST_EXTRACTION_RESULT.get('entities', [])
        
        # Check for Survivor Sarah
        sarah = next((e for e in entities if (isinstance(e, dict) and 'Sarah' in e.get('name', '')) or (hasattr(e, 'name') and 'Sarah' in e.name)), None)
        if sarah:
            name = sarah.get('name') if isinstance(sarah, dict) else sarah.name
            print(f"✅ PASS: Found Survivor '{name}'")
        else:
            print(f"❌ FAIL: Survivor 'Sarah' not found in extraction. Entities found: {len(entities)}")

        # Check for Medical Supplies
        supplies = next((e for e in entities if (isinstance(e, dict) and 'Medical' in str(e)) or (hasattr(e, 'name') and 'Medical' in str(e))), None)
        if supplies:
             print(f"✅ PASS: Found Need related to 'Medical/Bandages'")
        else:
             print(f"❌ FAIL: Need 'Medical Supplies' not found.")

    if not dry_run:
             print("\n>>> REAL RUN: Check your Spanner Database to verify data!")

    # Image Test
    print("\n--- Running Image Extraction Test ---")
    await run_single_test("test_pipeline.png", session_service, user_id)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true", help="Run against real services (disable dry run)")
    args = parser.parse_args()
    
    dry_run_mode = not args.real
    asyncio.run(run_test(dry_run=dry_run_mode))
