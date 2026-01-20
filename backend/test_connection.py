#!/usr/bin/env python3
"""
Test script to verify Spanner connection and GQL query execution.
"""
import asyncio
from services.spanner_service import SpannerService
from services.graph_service import GraphService
from config import settings

async def test_spanner_connection():
    """Test the Spanner connection and basic query execution."""
    print("=" * 60)
    print("Testing Spanner Connection")
    print("=" * 60)
    
    print(f"\nConfiguration:")
    print(f"  Project ID: {settings.PROJECT_ID}")
    print(f"  Instance ID: {settings.INSTANCE_ID}")
    print(f"  Database ID: {settings.DATABASE_ID}")
    print(f"  Graph Name: {settings.GRAPH_NAME}")
    print(f"  Credentials: {settings.GOOGLE_APPLICATION_CREDENTIALS}")
    
    try:
        # Initialize services
        print("\n1. Initializing SpannerService...")
        spanner_service = SpannerService()
        print("   ✓ SpannerService initialized successfully")
        
        print("\n2. Initializing GraphService...")
        graph_service = GraphService(spanner_service)
        print("   ✓ GraphService initialized successfully")
        
        # Test basic query
        print("\n3. Testing basic GQL query...")
        try:
            # Simple query to test connection
            query = "MATCH (n) RETURN n LIMIT 5"
            results = spanner_service.execute_gql(query)
            print(f"   ✓ Query executed successfully")
            print(f"   ✓ Found {len(results)} nodes")
            
            if results:
                print("\n   Sample result:")
                print(f"   {results[0]}")
        except Exception as e:
            print(f"   ✗ Query failed: {e}")
            print(f"   Note: This might be expected if the database is empty or the schema is different")
        
        # Test full graph retrieval
        print("\n4. Testing full graph retrieval...")
        try:
            graph_data = await graph_service.get_full_graph()
            print(f"   ✓ Graph data retrieved")
            print(f"   ✓ Nodes: {len(graph_data.nodes)}")
            print(f"   ✓ Edges: {len(graph_data.edges)}")
            
            if graph_data.nodes:
                print("\n   Sample node:")
                sample_node = graph_data.nodes[0]
                print(f"     ID: {sample_node.id}")
                print(f"     Type: {sample_node.type}")
                print(f"     Label: {sample_node.label}")
        except Exception as e:
            print(f"   ✗ Failed to get full graph: {e}")
        
        print("\n" + "=" * 60)
        print("Connection test completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        print("\nPlease check:")
        print("1. Your service account key path is correct in .env")
        print("2. The service account has Spanner permissions")
        print("3. The Spanner instance and database exist")
        print("4. The graph schema is properly configured")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_spanner_connection())
