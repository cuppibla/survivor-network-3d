import os
import logging
from google.cloud import spanner
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
INSTANCE_ID = os.getenv("INSTANCE_ID")
DATABASE_ID = os.getenv("DATABASE_ID")
GRAPH_NAME = os.getenv("GRAPH_NAME", "SurvivorGraph")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verification")

def verify_data():
    print(f"--- Configuration ---")
    print(f"Project:  {PROJECT_ID}")
    print(f"Instance: {INSTANCE_ID}")
    print(f"Database: {DATABASE_ID}")
    print(f"Graph:    {GRAPH_NAME}")
    print(f"---------------------\n")

    if not all([PROJECT_ID, INSTANCE_ID, DATABASE_ID]):
        print("ERROR: Missing environment variables. Check your .env file.")
        return

    try:
        client = spanner.Client(project=PROJECT_ID)
        instance = client.instance(INSTANCE_ID)
        database = instance.database(DATABASE_ID)

        print("1. Checking Broadcasts table...")
        with database.snapshot() as snapshot:
            results = snapshot.execute_sql(
                "SELECT broadcast_id, title, processed, created_at "
                "FROM Broadcasts WHERE processed = TRUE "
                "ORDER BY created_at DESC LIMIT 5"
            )
            rows = list(results)
            if rows:
                print(f"✅ Found {len(rows)} processed broadcasts:")
                for row in rows:
                    print(f"   - {row[1]} (ID: {row[0]})")
            else:
                print("❌ No processed broadcasts found in 'Broadcasts' table.")

        print("\n2. Checking Resources...")
        with database.snapshot() as snapshot:
            results = snapshot.execute_sql(
                "SELECT name, type, description FROM Resources "
                "WHERE name LIKE '%Crystal%' OR name LIKE '%Energy%' "
                "ORDER BY resource_id DESC LIMIT 5"
            )
            rows = list(results)
            if rows:
                print(f"✅ Found matching resources:")
                for row in rows:
                    print(f"   - {row[0]} ({row[1]})")
            else:
                print("❌ No resources matching 'Crystal' or 'Energy' found.")

        print("\n3. Checking Graph Edges (GQL)...")
        with database.snapshot() as snapshot:
            query = f"""
                GRAPH {GRAPH_NAME}
                MATCH (s:Survivor {{name: "David Chen"}})-[f:FOUND]->(r:Resource)
                RETURN s.name AS survivor, r.name AS resource
            """
            try:
                results = snapshot.execute_sql(query)
                rows = list(results)
                if rows:
                    print(f"✅ Found Graph connections for David Chen:")
                    for row in rows:
                        print(f"   - Found: {row[1]}")
                else:
                    print("❌ No 'FOUND' relationships for David Chen in graph.")
            except Exception as e:
                 print(f"❌ Graph query failed: {e}")

    except Exception as e:
        print(f"❌ Connection/Verification failed: {e}")

if __name__ == "__main__":
    verify_data()
