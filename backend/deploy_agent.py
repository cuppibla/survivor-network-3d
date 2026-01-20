import os
import logging
from dotenv import load_dotenv
import vertexai
from google.genai import types as genai_types
from vertexai.preview import reasoning_engines
from vertexai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
AGENT_DISPLAY_NAME = "survivor_network_agent_engine"

if not PROJECT_ID:
    raise ValueError("PROJECT_ID not found in environment variables.")

# Basic configuration types
MemoryBankConfig = types.ReasoningEngineContextSpecMemoryBankConfig
CustomizationConfig = types.MemoryBankCustomizationConfig
MemoryTopic = types.MemoryBankCustomizationConfigMemoryTopic
CustomMemoryTopic = types.MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic
GenerateMemoriesExample = types.MemoryBankCustomizationConfigGenerateMemoriesExample
ConversationSource = types.MemoryBankCustomizationConfigGenerateMemoriesExampleConversationSource
ConversationSourceEvent = types.MemoryBankCustomizationConfigGenerateMemoriesExampleConversationSourceEvent
ExampleGeneratedMemory = types.MemoryBankCustomizationConfigGenerateMemoriesExampleGeneratedMemory
Content = genai_types.Content
Part = genai_types.Part

def register_agent_engine():
    """
    Registers an Agent Engine resource in Vertex AI to enable Sessions and Memory Bank.
    """
    logger.info(f"Initializing Vertex AI for project: {PROJECT_ID}, location: {LOCATION}")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

    # --- Define Custom Topics ---
    logger.info("Defining custom topics...")
    
    custom_topics = [
        # Topic 1: Survivor Identity & Skills
        MemoryTopic(
            custom_memory_topic=CustomMemoryTopic(
                label="survivor_identity",
                description="""Extract the user's survivor identity, including:
                - Name
                - Profession/Role (e.g., Doctor, Engineer, Scavenger)
                - Key Skills (e.g., First Aid, Mechanics, Farming)
                - Background details
                
                Example: "User is a former urgent care nurse named Sarah with advanced first aid skills."
                """,
            )
        ),
        # Topic 2: Current Status & Inventory
        MemoryTopic(
            custom_memory_topic=CustomMemoryTopic(
                label="survivor_status",
                description="""Track the user's current condition and resources:
                - Health status (injured, sick, healthy)
                - Key inventory items (medkits, weapons, food supply)
                - Current location or shelter status
                
                Example: "User has a broken leg and is low on antibiotics."
                Example: "User has a stockpile of canned food and clean water."
                """,
            )
        ),
         # Topic 3: Goals & Missions
        MemoryTopic(
            custom_memory_topic=CustomMemoryTopic(
                label="survivor_goals",
                description="""Track the user's current objectives and missions:
                - Immediate goals (find water, repair radio)
                - Long-term goals (find other survivors, reach the coast)
                
                Example: "User is currently trying to repair the radio tower to contact help."
                """,
            )
        )
    ]

    # --- Define Few-Shot Examples ---
    logger.info("Defining few-shot examples...")
    
    few_shot_examples = [
        GenerateMemoriesExample(
            conversation_source=ConversationSource(
                events=[
                    ConversationSourceEvent(
                        content=Content(
                            role="user",
                            parts=[Part(text="My name is Jack, I used to be a construction worker before everything fell apart. I'm good at building reinforcements.")]
                        )
                    ),
                    ConversationSourceEvent(
                        content=Content(
                            role="model",
                            parts=[Part(text="Welcome Jack. Your construction skills will be vital for fortifying our shelter. Do you have any tools with you?")]
                        )
                    ),
                    ConversationSourceEvent(
                        content=Content(
                            role="user",
                            parts=[Part(text="I managed to save my toolbelt, so I have a hammer and some basic tools. But I'm running low on nails.")]
                        )
                    )
                ]
            ),
            generated_memories=[
                ExampleGeneratedMemory(fact="User's name is Jack"),
                ExampleGeneratedMemory(fact="User was a construction worker"),
                ExampleGeneratedMemory(fact="User is skilled at building reinforcements"),
                ExampleGeneratedMemory(fact="User has a hammer and basic tools"),
                ExampleGeneratedMemory(fact="User is running low on nails")
            ]
        ),
        GenerateMemoriesExample(
            conversation_source=ConversationSource(
                events=[
                    ConversationSourceEvent(
                        content=Content(
                            role="user",
                            parts=[Part(text="I'm injured. A wolf attacked me while I was scavenging. My leg is bleeding bad.")]
                        )
                    ),
                    ConversationSourceEvent(
                        content=Content(
                            role="model",
                            parts=[Part(text="That sounds serious! You need to stop the bleeding immediately. Do you have any bandages or a first aid kit?")]
                        )
                    ),
                    ConversationSourceEvent(
                        content=Content(
                            role="user",
                            parts=[Part(text="No, I used my last bandage yesterday. I need to find a pharmacy.")]
                        )
                    )
                ]
            ),
            generated_memories=[
                ExampleGeneratedMemory(fact="User entered 'injured' status due to wolf attack"),
                ExampleGeneratedMemory(fact="User has a bleeding leg injury"),
                ExampleGeneratedMemory(fact="User has no bandages remaining"),
                ExampleGeneratedMemory(fact="User's immediate goal is to find a pharmacy")
            ]
        )
    ]

    # --- Create Customization Config ---
    customization_config = CustomizationConfig(
        memory_topics=custom_topics,
        generate_memories_examples=few_shot_examples
    )

    logger.info(f"Creating/Registering Agent Engine: {AGENT_DISPLAY_NAME}")
    
    # Create Agent Engine with Memory Bank configuration
    agent_engine = client.agent_engines.create(
        config={
            "display_name": AGENT_DISPLAY_NAME,
            "context_spec": {
                "memory_bank_config": {
                    "generation_config": {
                        "model": f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/gemini-2.5-flash"
                    },
                    "customization_configs": [customization_config]
                }
            },
        }
    )

    agent_engine_id = agent_engine.api_resource.name.split("/")[-1]
    logger.info("✅ Agent Engine Registered Successfully!")
    logger.info(f"Agent Engine ID: {agent_engine_id}")
    logger.info("\nIMPORTANT: Add the following line to your backend/.env file:")
    logger.info(f"AGENT_ENGINE_ID={agent_engine_id}")

if __name__ == "__main__":
    try:
        register_agent_engine()
    except Exception as e:
        logger.error(f"Failed to register Agent Engine: {e}")
