import os
import asyncio
from google.adk import Runner
from google.genai.types import Content, Part
from agent.multimedia_agent import uploader_agent
from config import settings
from google.cloud import storage
import uuid

if settings.GOOGLE_API_KEY and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

# Test files configuration
TEST_FILES = [
    "test_upload.txt",
    "test_image.png",
    "test_video.mp4"
]

def setup_test_files():
    """Ensures dummmy test files exist."""
    if "test_upload.txt" not in os.listdir("."):
        with open("test_upload.txt", "w") as f:
            f.write("This is a test file for GCS upload verification.")
    
    # helper for creating dummy binary files if missing
    def create_dummy_binary(filename, size=1024):
        if filename not in os.listdir("."):
             with open(filename, "wb") as f:
                 f.write(os.urandom(size))

    create_dummy_binary("test_image.png")
    create_dummy_binary("test_video.mp4")

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

async def run_single_upload(runner, session_service, file_path, user_id="test-user"):
    """Runs a single upload test for a given file."""
    print(f"\n--- Testing upload for: {file_path} ---")
    abs_path = os.path.abspath(file_path)
    
    # Construct the user message
    message_text = f"Attached file path: {abs_path}"
    user_msg = Content(role="user", parts=[Part(text=message_text)])
    
    app_name = f"test-uploader-{uuid.uuid4().hex[:6]}"
    session = await session_service.create_session(user_id=user_id, app_name=app_name)
    print(f"Created session {session.id}")
    
    print("Invoking agent...")
    gcs_uri = None
    
    try:
        async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=user_msg):
            # The uploader_agent is instructed to output *only* the GCS URI.
            if hasattr(event, "text") and event.text:
                print(f"Agent Output: {event.text}")
                if "gs://" in event.text:
                    gcs_uri = event.text.strip()
            elif hasattr(event, "content") and event.content:
                 for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        print(f"Agent Content: {part.text}")
                        if "gs://" in part.text:
                             gcs_uri = part.text.strip()
                        
    except Exception as e:
        print(f"Agent execution failed: {e}")
        import traceback
        traceback.print_exc()
        
    if gcs_uri:
        print(f"SUCCESS: {file_path} uploaded. URI: {gcs_uri}")
        return True
    else:
        print(f"FAILURE: {file_path} - No GCS URI returned.")
        return False

async def run_test():
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
    
    # Initialize Runner with uploader_agent
    from google.adk.sessions import InMemorySessionService
    session_service = InMemorySessionService()
    runner = Runner(agent=uploader_agent, app_name="test-uploader", session_service=session_service)
    
    results = {}
    for test_file in TEST_FILES:
        success = await run_single_upload(runner, session_service, test_file)
        results[test_file] = success

    print("\n\n=== FINAL RESULTS ===")
    for filename, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"{filename}: {status}")

    # Cleanup (optional - maybe we want to keep them for manual verification? 
    # The previous script deleted the text file. Let's keep them this time or delete only generated ones if we wanted to be strict.
    # The user asked 'how to verify', so keeping the bucket is good. We usually don't delete the bucket in this script.)

if __name__ == "__main__":
    asyncio.run(run_test())
