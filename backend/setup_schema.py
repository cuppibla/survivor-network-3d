"""
Spanner Graph Schema Setup Script
This script creates the SurvivorGraph property graph schema in your Spanner database.
"""

from google.cloud import spanner
from config import settings
import os

# Set credentials
if settings.GOOGLE_APPLICATION_CREDENTIALS:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GOOGLE_APPLICATION_CREDENTIALS

def create_graph_schema():
    """Create the SurvivorGraph schema with nodes and edges."""
    
    client = spanner.Client(project=settings.PROJECT_ID)
    instance = client.instance(settings.INSTANCE_ID)
    database = instance.database(settings.DATABASE_ID)
    
    print("=" * 60)
    print("Creating Spanner Graph Schema: SurvivorGraph")
    print("=" * 60)
    
    # DDL statements to create the graph schema
    ddl_statements = [
        # Create node tables
        """
        CREATE TABLE Survivors (
            id STRING(36) NOT NULL,
            label STRING(100),
            role STRING(100),
            biome STRING(50),
        ) PRIMARY KEY (id)
        """,
        
        """
        CREATE TABLE Skills (
            id STRING(36) NOT NULL,
            label STRING(100),
            level STRING(50),
        ) PRIMARY KEY (id)
        """,
        
        """
        CREATE TABLE Needs (
            id STRING(36) NOT NULL,
            label STRING(100),
            urgency STRING(50),
        ) PRIMARY KEY (id)
        """,
        
        # Create edge tables
        """
        CREATE TABLE HasSkill (
            id STRING(36) NOT NULL,
            survivor_id STRING(36) NOT NULL,
            skill_id STRING(36) NOT NULL,
            FOREIGN KEY (survivor_id) REFERENCES Survivors(id),
            FOREIGN KEY (skill_id) REFERENCES Skills(id),
        ) PRIMARY KEY (id)
        """,
        
        """
        CREATE TABLE HasNeed (
            id STRING(36) NOT NULL,
            survivor_id STRING(36) NOT NULL,
            need_id STRING(36) NOT NULL,
            FOREIGN KEY (survivor_id) REFERENCES Survivors(id),
            FOREIGN KEY (need_id) REFERENCES Needs(id),
        ) PRIMARY KEY (id)
        """,
        
        """
        CREATE TABLE Treats (
            id STRING(36) NOT NULL,
            skill_id STRING(36) NOT NULL,
            need_id STRING(36) NOT NULL,
            effectiveness STRING(50),
            FOREIGN KEY (skill_id) REFERENCES Skills(id),
            FOREIGN KEY (need_id) REFERENCES Needs(id),
        ) PRIMARY KEY (id)
        """,
        
        # Create the property graph
        """
        CREATE PROPERTY GRAPH SurvivorGraph
        NODE TABLES (
            Survivors AS Survivor
                KEY (id)
                LABEL Survivor
                PROPERTIES (id, label, role, biome),
            Skills AS Skill
                KEY (id)
                LABEL Skill
                PROPERTIES (id, label, level),
            Needs AS Need
                KEY (id)
                LABEL Need
                PROPERTIES (id, label, urgency)
        )
        EDGE TABLES (
            HasSkill AS HAS_SKILL
                KEY (id)
                SOURCE KEY (survivor_id) REFERENCES Survivor(id)
                DESTINATION KEY (skill_id) REFERENCES Skill(id)
                LABEL HAS_SKILL,
            HasNeed AS HAS_NEED
                KEY (id)
                SOURCE KEY (survivor_id) REFERENCES Survivor(id)
                DESTINATION KEY (need_id) REFERENCES Need(id)
                LABEL HAS_NEED,
            Treats AS TREATS
                KEY (id)
                SOURCE KEY (skill_id) REFERENCES Skill(id)
                DESTINATION KEY (need_id) REFERENCES Need(id)
                LABEL TREATS
                PROPERTIES (effectiveness)
        )
        """
    ]
    
    try:
        print("\nExecuting DDL statements...")
        operation = database.update_ddl(ddl_statements)
        
        print("Waiting for operation to complete...")
        operation.result(timeout=120)
        
        print("✓ Graph schema created successfully!")
        print("\nCreated:")
        print("  - Node tables: Survivors, Skills, Needs")
        print("  - Edge tables: HasSkill, HasNeed, Treats")
        print("  - Property graph: SurvivorGraph")
        
    except Exception as e:
        print(f"✗ Error creating schema: {e}")
        print("\nIf tables already exist, you may need to drop them first or modify the schema.")
        return False
    
    return True


def insert_sample_data():
    """Insert sample data into the graph."""
    
    client = spanner.Client(project=settings.PROJECT_ID)
    instance = client.instance(settings.INSTANCE_ID)
    database = instance.database(settings.DATABASE_ID)
    
    print("\n" + "=" * 60)
    print("Inserting Sample Data")
    print("=" * 60)
    
    def insert_data(transaction):
        # Insert survivors
        transaction.execute_update(
            "INSERT INTO Survivors (id, label, role, biome) VALUES "
            "('n1', 'Frost', 'Xenobiologist', 'CRYO'), "
            "('n2', 'Tanaka', 'Captain', 'FOSSILIZED')"
        )
        
        # Insert skills
        transaction.execute_update(
            "INSERT INTO Skills (id, label, level) VALUES "
            "('n3', 'Medical Training', 'Expert')"
        )
        
        # Insert needs
        transaction.execute_update(
            "INSERT INTO Needs (id, label, urgency) VALUES "
            "('n4', 'Burns', 'High')"
        )
        
        # Insert edges
        transaction.execute_update(
            "INSERT INTO HasSkill (id, survivor_id, skill_id) VALUES "
            "('e1', 'n1', 'n3')"
        )
        
        transaction.execute_update(
            "INSERT INTO HasNeed (id, survivor_id, need_id) VALUES "
            "('e2', 'n2', 'n4')"
        )
        
        transaction.execute_update(
            "INSERT INTO Treats (id, skill_id, need_id, effectiveness) VALUES "
            "('e3', 'n3', 'n4', 'High')"
        )
    
    try:
        database.run_in_transaction(insert_data)
        print("✓ Sample data inserted successfully!")
        print("\nInserted:")
        print("  - 2 Survivors: Frost, Tanaka")
        print("  - 1 Skill: Medical Training")
        print("  - 1 Need: Burns")
        print("  - 3 Relationships")
        
    except Exception as e:
        print(f"✗ Error inserting data: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print(f"Project: {settings.PROJECT_ID}")
    print(f"Instance: {settings.INSTANCE_ID}")
    print(f"Database: {settings.DATABASE_ID}\n")
    
    # Create schema
    if create_graph_schema():
        # Insert sample data
        insert_sample_data()
        
        print("\n" + "=" * 60)
        print("Setup Complete!")
        print("=" * 60)
        print("\nYou can now run: python3 test_connection.py")
    else:
        print("\nSetup failed. Please check the errors above.")
