
import asyncio
import os
import sys

# Ensure backend path is in sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from agent.agent import root_agent

async def debug_loop():
    print("DEBUG: Starting Debug Loop")
    
    # Setup mock services in-memory
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        session_service=session_service,
        app_name="survivor-network"
    )
    
    user_id = "debug-user"
    session = await session_service.create_session(user_id=user_id, app_name="survivor-network")
    session_id = session.id
    print(f"DEBUG: Session Created: {session_id}")
    
    # Simulate attachments
    # We will pretend we have 2 files. 
    # Since we don't want to rely on actual files, we can just pass text paths that point to existing files
    # or create dummy files.
    
    # Create dummy files
    files = ["test_1.txt", "test_2.txt"]
    for f in files:
        with open(f, "w") as f_obj:
            f_obj.write(f"Dummy content for {f}")
            
    print(f"DEBUG: Created dummy files: {files}")

    response_text = ""
    
    async def run_agent_cycle(parts):
        nonlocal response_text
        print("DEBUG: Running agent cycle...")
        async for event in runner.run_async(
            user_id=user_id, 
            session_id=session_id, 
            new_message=Content(role="user", parts=parts)
        ):
            # Just consume events
            pass
        response_text += "Cycle Done.\n"
        print("DEBUG: Agent cycle complete.")

    try:
        # Loop logic from chat.py
        total_files = len(files)
        for i, file_path in enumerate(files):
            print(f"DEBUG: Processing attachment {i+1}/{total_files}: {file_path}")
            
            current_parts = []
            if i == 0:
                 current_parts.append(Part(text="Here are some files."))
            else:
                 current_parts.append(Part(text=f"Processing next attachment ({i+1}/{total_files})..."))

            # Mock file reading (just passing path text as we do in chat.py)
            current_parts.append(Part(text=f"\n[System] Attached file path: {os.path.abspath(file_path)}"))
            
            # Run the cycle
            await run_agent_cycle(current_parts)
            
    finally:
        # Cleanup
        for f in files:
            if os.path.exists(f):
                os.remove(f)

    print("DEBUG: Loop Finished")

if __name__ == "__main__":
    asyncio.run(debug_loop())
