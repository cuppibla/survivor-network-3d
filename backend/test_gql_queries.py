"""
Test updated GQL queries with correct syntax
"""

import asyncio
from services.spanner_service import SpannerService
from services.graph_service import GraphService
from config import settings

async def test_updated_queries():
    """Test the corrected GQL queries."""
    
    print("=" * 60)
    print("Testing Updated GQL Queries")
    print("=" * 60)
    
    spanner = SpannerService()
    graph_service = GraphService(spanner)
    
    # Test 1: Direct table query
    print("\n1. Testing direct table queries...")
    try:
        # Get count of survivors
        query_survivors = "SELECT COUNT(*) as count FROM Survivors"
        result = spanner.database.snapshot().execute_sql(query_survivors)
        for row in result:
            print(f"   ✓ Found {row[0]} survivors in database")
        
        # Get count of skills
        query_skills = "SELECT COUNT(*) as count FROM Skills"
        result = spanner.database.snapshot().execute_sql(query_skills)
        for row in result:
            print(f"   ✓ Found {row[0]} skills in database")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Simple GQL query with properties
    print("\n2. Testing GQL query with properties...")
    try:
        query = """
        GRAPH SurvivorGraph
        MATCH (s:Survivor)
        RETURN s.survivor_id, s.name, s.role
        LIMIT 5
        """
        result = spanner.database.snapshot().execute_sql(query)
        count = 0
        for row in result:
            count += 1
            print(f"   ✓ Survivor: {row[1]} ({row[2]})")
        print(f"   Total: {count} survivors")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Get full graph
    print("\n3. Testing full graph retrieval...")
    try:
        graph_data = await graph_service.get_full_graph()
        print(f"   ✓ Nodes: {len(graph_data.nodes)}")
        print(f"   ✓ Edges: {len(graph_data.edges)}")
        
        if graph_data.nodes:
            print("\n   Sample nodes:")
            for node in graph_data.nodes[:3]:
                print(f"     - {node.label} ({node.type})")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_updated_queries())
