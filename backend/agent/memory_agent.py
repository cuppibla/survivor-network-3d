from google.adk.agents import Agent
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from typing import Optional
from config import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

# Instruction for the memory agent
memory_agent_instruction = """
You are a Memory Assistant.
Your goal is to passively observe the conversation and manage the user's memory bank context.
You have access to the user's memory bank tools.
"""

async def add_session_to_memory(
        callback_context: CallbackContext
) -> Optional[types.Content]:
    """Automatically save completed sessions to memory bank in the background"""
    if hasattr(callback_context, "_invocation_context"):
        invocation_context = callback_context._invocation_context
        if invocation_context.memory_service:
            # Use create_task to run this in the background without blocking the response
            asyncio.create_task(
                invocation_context.memory_service.add_session_to_memory(
                    invocation_context.session
                )
            )
            logger.info("Scheduled session save to memory bank in background")

agent_tools = []
if settings.USE_MEMORY_BANK:
    agent_tools.append(PreloadMemoryTool())

memory_agent = Agent(
    model="gemini-2.5-flash",
    name="memory_agent",
    instruction=memory_agent_instruction,
    tools=agent_tools,
    after_agent_callback=add_session_to_memory if settings.USE_MEMORY_BANK else None
)
