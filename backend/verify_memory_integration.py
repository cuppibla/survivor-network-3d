
import asyncio
import logging
import os
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import settings
from config import settings

# Put global patch here
patcher = patch("services.spanner_graph_service.SpannerGraphService")
patcher.start()
patch("services.gcs_service.GCSService").start()
# Also mock extractors to avoid any other init
patch("extractors.text_extractor.TextExtractor").start()
patch("extractors.image_extractor.ImageExtractor").start()
patch("extractors.video_extractor.VideoExtractor").start()

async def run_verification():
    print("--- Starting Memory Integration Verification ---")
    
    # Imports inside verification to ensure fresh/patched context
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai.types import Content, Part
    
    # We are inside the patch context now
    from agent.multimedia_agent import multimedia_agent, spanner_agent
    
    # Verify spanner_agent has the callback
    print(f"DEBUG: Spanner Agent Callback: {spanner_agent.after_agent_callback}")
    
    # Setup mocks for tools
    with patch("agent.multimedia_agent.add_session_to_memory") as mock_memory_callback, \
         patch("agent.multimedia_agent.upload_media") as mock_upload, \
         patch("agent.multimedia_agent.extract_from_media") as mock_extract, \
         patch("agent.multimedia_agent.save_to_spanner") as mock_save:
            
        mock_upload.return_value = {
            "status": "success", 
            "gcs_uri": "gs://test/file.txt", 
            "media_type": "text",
            "file_name": "file.txt"
        }
        mock_extract.return_value = {
            "extraction_result": {"entities": [], "relationships": []},
            "summary": "Extracted stuff",
            "entities_count": 0,
            "relationships_count": 0
        }
        mock_save.return_value = {
            "status": "success",
            "entities_created": 1,
            "entities_found_existing": 0,
            "relationships_created": 0,
            "broadcast_id": "test-id",
            "errors": None
        }
        
        # Test Runner
        session_service = InMemorySessionService()
        runner = Runner(agent=multimedia_agent, app_name="test-app", session_service=session_service)
        session = await session_service.create_session(user_id="test-user", app_name="test-app")
        
        print(">>> Running Agent Pipeline...")
        user_msg = Content(role="user", parts=[Part(text="Upload file.txt")])
        
        async for event in runner.run_async(user_id="test-user", session_id=session.id, new_message=user_msg):
            if hasattr(event, "text") and event.text:
                print(f"Agent Output: {event.text}")
        
        print("\n>>> Verification Results:")
        
        if mock_save.called:
             print("✅ PASS: Spanner Agent executed save_to_spanner")
        else:
             print("❌ FAIL: Spanner Agent did not save to database")

        if spanner_agent.after_agent_callback:
             print("✅ PASS: Callback IS attached to Spanner Agent")
        else:
             print("❌ FAIL: Callback is NOT attached.")

        if mock_memory_callback.called:
            print("✅ PASS: Memory Callback execution triggered")
            print(f"   Call count: {mock_memory_callback.call_count}")
        else:
            print("❌ FAIL: Memory Callback NOT triggered")

if __name__ == "__main__":
    # Patch settings.USE_MEMORY_BANK to True
    with patch("config.settings.settings.USE_MEMORY_BANK", True):
        asyncio.run(run_verification())
