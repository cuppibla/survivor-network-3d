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

def check_new_data():
    if not all([PROJECT_ID, INSTANCE_ID, DATABASE_ID]):
        print("ERROR: Missing config")
        return

    client = spanner.Client(project=PROJECT_ID)
    instance = client.instance(INSTANCE_ID)
    database = instance.database(DATABASE_ID)

    print(f"Checking updates for Elena Frost and Yuki Tanaka in {DATABASE_ID}...")

    with database.snapshot(multi_use=True) as snapshot:
        # 1. Check Broadcasts
        print("\n[Broadcasts Check]")
        results = snapshot.execute_sql(
            "SELECT title, processed, created_at FROM Broadcasts "
            "ORDER BY created_at DESC LIMIT 5"
        )
        for row in results:
            print(f"- {row[0]} (Processed: {row[1]})")

        # 2. Check Graph for Elena (Cryo)
        print("\n[Elena Frost Graph Check]")
        query_elena = f"""
            GRAPH {GRAPH_NAME}
            MATCH (s:Survivor)-[i:IN_BIOME]->(b:Biome)
            WHERE s.name = "Dr. Elena Frost"
            RETURN s.name AS survivor, b.name AS biome
        """
        results_elena = snapshot.execute_sql(query_elena)
        found_elena = False
        for row in results_elena:
            print(f"✅ Found: {row[0]} in {row[1]}")
            found_elena = True
        if not found_elena:
            print("❌ No 'IN_BIOME' edge found for Dr. Elena Frost")

        # 3. Check Graph for Yuki (Geothermal)
        print("\n[Yuki Tanaka Graph Check]")
        query_yuki = f"""
            GRAPH {GRAPH_NAME}
            MATCH (s:Survivor)-[f:FOUND]->(r:Resource)
            WHERE s.name = "Captain Yuki Tanaka"
            RETURN s.name AS survivor, r.name AS resource
        """
        results_yuki = snapshot.execute_sql(query_yuki)
        found_yuki = False
        for row in results_yuki:
            print(f"✅ Found: {row[0]} found {row[1]}")
            found_yuki = True
        if not found_yuki:
             print("❌ No 'FOUND' edge found for Captain Yuki Tanaka")

if __name__ == "__main__":
    check_new_data()
