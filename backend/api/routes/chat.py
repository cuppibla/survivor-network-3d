from fastapi import APIRouter
from models.chat import ChatRequest, ChatResponse
from agent.agent import root_agent

from google.adk import Runner
from google.adk.sessions import InMemorySessionService, VertexAiSessionService
from google.adk.memory import InMemoryMemoryService, VertexAiMemoryBankService
from google.genai.types import Content, Part
from config import settings
import os
import time

router = APIRouter()

# Initialize Services
# Ensure API Key is set for GenAI client
if settings.GOOGLE_API_KEY and "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

if settings.USE_MEMORY_BANK and settings.AGENT_ENGINE_ID:
    print(f"INFO: Initializing Vertex AI Services with Agent Engine: {settings.AGENT_ENGINE_ID}")
    session_service = VertexAiSessionService(
        project=settings.PROJECT_ID, 
        location=settings.LOCATION, 
        agent_engine_id=settings.AGENT_ENGINE_ID
    )
    memory_service = VertexAiMemoryBankService(
        project=settings.PROJECT_ID, 
        location=settings.LOCATION, 
        agent_engine_id=settings.AGENT_ENGINE_ID
    )
else:
    print("INFO: Initializing InMemory Services")
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()

# Initialize Runner
# For sub-agents using memory bank, we must ensure memory service is passed to the runner
runner = Runner(
    agent=root_agent, 
    session_service=session_service,
    memory_service=memory_service,
    app_name="survivor-network"
)

# Global session map to persist mapping between client conversation_ids and ADK session_ids
# Note: In a production environment with multiple workers, this should be in Redis or database
SESSION_MAP = {} 

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        user_id = "test-user" # In a real app, get this from auth
        conversation_id = request.conversation_id or "default-session"
        
        # Check if we have an existing session_id providing mapping
        if conversation_id in SESSION_MAP:
            session_id = SESSION_MAP[conversation_id]
            print(f"DEBUG: Found existing session {session_id} for conversation {conversation_id}")
            
            # Verify session still exists (especially for in-memory)
            try:
                await session_service.get_session(app_name="survivor-network", session_id=session_id, user_id=user_id)
            except Exception:
                print(f"DEBUG: Session {session_id} not found, creating new one.")
                session_id = None
        else:
            session_id = None
            
        if not session_id:
            # Create a new session
            session = await session_service.create_session(user_id=user_id, app_name="survivor-network")
            print(f"DEBUG: Created new session {session.id}")
            session_id = session.id
            SESSION_MAP[conversation_id] = session_id
        
        # Accumulate response text
        response_text = ""
        
        # Prepare message parts
        message_parts = [Part(text=request.message)]
        if request.attachments:
            for attachment in request.attachments:
                try:
                    with open(attachment["path"], "rb") as f:
                        file_data = f.read()
                        message_parts.append(Part.from_bytes(data=file_data, mime_type=attachment["mime_type"]))
                    # Append file path as text context for the agent tools
                    message_parts.append(Part(text=f"\n[System] Attached file path: {attachment['path']}"))
                except Exception as e:
                    print(f"Error reading attachment {attachment['path']}: {e}")

        # Execute agent using Runner
        # Wrap message in Content object as required by Runner
        async for event in runner.run_async(
            user_id=user_id, 
            session_id=session_id, 
            new_message=Content(role="user", parts=message_parts)
        ):
            # Inspect event structure to find text content
            try:
                # Check for standard response structures
                if hasattr(event, "text") and event.text:
                    response_text += event.text
                elif hasattr(event, "content") and event.content:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text
                elif hasattr(event, "parts"):
                     for part in event.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text
            except Exception as e:
                # Log internal processing errors but continue
                print(f"Error processing event: {e}")
                pass
                
        if not response_text:
            response_text = "I received your message, but I couldn't generate a text response."

        return ChatResponse(
            answer=response_text,
            gql_query=None,
            nodes_to_highlight=[],
            edges_to_highlight=[],
            suggested_followups=[]
        )
    except Exception as e:
        import traceback
        error_msg = f"Error processing message: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return ChatResponse(
            answer=error_msg,
            gql_query=None,
            nodes_to_highlight=[],
            edges_to_highlight=[],
            suggested_followups=[]
        )
