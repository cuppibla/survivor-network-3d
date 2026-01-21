import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

try:
    print("Testing imports...")
    from backend.services.hybrid_search_service import HybridSearchService
    from backend.agent.tools.hybrid_search_tools import hybrid_search, _get_service
    from backend.agent.agent import root_agent
    
    print("Imports successful!")
    
    print("Checking agent tools...")
    tool_names = [t.__name__ for t in root_agent.tools]
    expected_tools = [
        "hybrid_search", 
        "semantic_search", 
        "keyword_search", 
        "find_similar_skills", 
        "analyze_query"
    ]
    
    for tool in expected_tools:
        if tool in tool_names:
            print(f"✅ Tool '{tool}' registered successfully")
        else:
            print(f"❌ Tool '{tool}' NOT found in agent")
            
    print("\nVerification complete!")

except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
