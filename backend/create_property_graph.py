"""
Create property graph definition matching the existing schema
"""

from google.cloud import spanner
from config import settings
import os

# Set credentials
if settings.GOOGLE_APPLICATION_CREDENTIALS:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GOOGLE_APPLICATION_CREDENTIALS

def create_property_graph():
    """Create SurvivorGraph property graph using existing tables."""
    
    client = spanner.Client(project=settings.PROJECT_ID)
    instance = client.instance(settings.INSTANCE_ID)
    database = instance.database(settings.DATABASE_ID)
    
    print("=" * 60)
    print("Creating Property Graph: SurvivorGraph")
    print("=" * 60)
    
    # DDL to create property graph using existing tables
    ddl_statements = [
        """
        CREATE OR REPLACE PROPERTY GRAPH SurvivorGraph
        NODE TABLES (
            Survivors AS Survivor
                KEY (survivor_id)
                LABEL Survivor
                PROPERTIES (survivor_id, name, callsign, role, biome, quadrant, status, avatar_url, color, x_position, y_position, description),
            Skills AS Skill
                KEY (skill_id)
                LABEL Skill
                PROPERTIES (skill_id, name, category, icon, color, description),
            Needs AS Need
                KEY (need_id)
                LABEL Need
                PROPERTIES (need_id, description, category, urgency, icon),
            Resources AS Resource
                KEY (resource_id)
                LABEL Resource
                PROPERTIES (resource_id, name, type, icon, biome, description),
            Biomes AS Biome
                KEY (biome_id)
                LABEL Biome
                PROPERTIES (biome_id, name, quadrant, color, icon, description)
        )
        EDGE TABLES (
            SurvivorHasSkill AS HAS_SKILL
                KEY (survivor_id, skill_id)
                SOURCE KEY (survivor_id) REFERENCES Survivor(survivor_id)
                DESTINATION KEY (skill_id) REFERENCES Skill(skill_id)
                LABEL HAS_SKILL
                PROPERTIES (proficiency),
            SurvivorHasNeed AS HAS_NEED
                KEY (survivor_id, need_id)
                SOURCE KEY (survivor_id) REFERENCES Survivor(survivor_id)
                DESTINATION KEY (need_id) REFERENCES Need(need_id)
                LABEL HAS_NEED
                PROPERTIES (status),
            SkillTreatsNeed AS TREATS
                KEY (skill_id, need_id)
                SOURCE KEY (skill_id) REFERENCES Skill(skill_id)
                DESTINATION KEY (need_id) REFERENCES Need(need_id)
                LABEL TREATS
                PROPERTIES (effectiveness),
            SurvivorCanHelp AS CAN_HELP
                KEY (helper_id, helpee_id)
                SOURCE KEY (helper_id) REFERENCES Survivor(survivor_id)
                DESTINATION KEY (helpee_id) REFERENCES Survivor(survivor_id)
                LABEL CAN_HELP
                PROPERTIES (reason, match_score, skill_id, need_id),
            SurvivorFoundResource AS FOUND
                KEY (survivor_id, resource_id)
                SOURCE KEY (survivor_id) REFERENCES Survivor(survivor_id)
                DESTINATION KEY (resource_id) REFERENCES Resource(resource_id)
                LABEL FOUND
                PROPERTIES (found_at),
            SurvivorInBiome AS IN_BIOME
                KEY (survivor_id, biome_id)
                SOURCE KEY (survivor_id) REFERENCES Survivor(survivor_id)
                DESTINATION KEY (biome_id) REFERENCES Biome(biome_id)
                LABEL IN_BIOME
        )
        """
    ]
    
    try:
        print("\nCreating property graph using existing tables...")
        print("Node types: Survivor, Skill, Need, Resource, Biome")
        print("Edge types: HAS_SKILL, HAS_NEED, TREATS, CAN_HELP, FOUND, IN_BIOME")
        
        operation = database.update_ddl(ddl_statements)
        
        print("\nWaiting for operation to complete...")
        operation.result(timeout=120)
        
        print("✓ Property graph 'SurvivorGraph' created successfully!")
        
    except Exception as e:
        print(f"✗ Error creating property graph: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print(f"Project: {settings.PROJECT_ID}")
    print(f"Instance: {settings.INSTANCE_ID}")
    print(f"Database: {settings.DATABASE_ID}\n")
    
    if create_property_graph():
        print("\n" + "=" * 60)
        print("Setup Complete!")
        print("=" * 60)
        print("\nNext: Run 'python3 test_connection.py' to verify")
    else:
        print("\nSetup failed. Please check the errors above.")
