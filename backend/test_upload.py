import os
import asyncio
from google.adk import Runner
from google.genai.types import Content, Part
from agent.multimedia_agent import uploader_agent
from config import settings

if settings.GOOGLE_API_KEY and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

# Create a dummy file to upload
TEST_FILE = "test_upload.txt"
with open(TEST_FILE, "w") as f:
    f.write("This is a test file for GCS upload verification.")

async def run_test():
    print(f"Starting test with file: {os.path.abspath(TEST_FILE)}")
    
    # Initialize Runner with uploader_agent
    from google.adk.sessions import InMemorySessionService
    session_service = InMemorySessionService()
    runner = Runner(agent=uploader_agent, app_name="test-uploader", session_service=session_service)
    
    # Construct the user message as expected by the agent instruction
    message_text = f"Attached file path: {os.path.abspath(TEST_FILE)}"
    user_msg = Content(role="user", parts=[Part(text=message_text)])
    
    session = await session_service.create_session(user_id="test-user", app_name="test-uploader")
    print(f"Created session {session.id}")
    
    print("Invoking agent...")
    gcs_uri = None
    
    try:
        async for event in runner.run_async(user_id="test-user", session_id=session.id, new_message=user_msg):
            # The uploader_agent is instructed to output *only* the GCS URI.
            # We look for text events.
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
        print(f"SUCCESS: File uploaded. URI: {gcs_uri}")
    else:
        print("FAILURE: No GCS URI returned.")

    # Cleanup
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

if __name__ == "__main__":
    asyncio.run(run_test())
