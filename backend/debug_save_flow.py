import os
import logging
from dotenv import load_dotenv
from services.spanner_graph_service import SpannerGraphService
from extractors.base_extractor import ExtractionResult, ExtractedEntity, ExtractedRelationship, EntityType, RelationshipType

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)

def test_save():
    print("--- Testing Spanner Save Logic ---")
    
    service = SpannerGraphService()
    
    # Create valid mock data matching the "Field Report" scenario
    mock_result = ExtractionResult(
        media_uri="gs://mock-bucket/debug_image.png",
        media_type="image",
        summary="Debug test summary",
        entities=[
            ExtractedEntity(
                entity_type=EntityType.SURVIVOR,
                name="David Chen",
                properties={"role": "Engineer"}
            ),
            ExtractedEntity(
                entity_type=EntityType.RESOURCE,
                name="Debug Crystal", 
                properties={"type": "power", "description": "A test crystal"}
            ),
            ExtractedEntity(
                entity_type=EntityType.BIOME,
                name="Bioluminescent",
                properties={}
            )
        ],
        relationships=[
            ExtractedRelationship(
                relationship_type=RelationshipType.FOUND_RESOURCE,
                source_name="David Chen",
                target_name="Debug Crystal",
                properties={"found_at": "2026-01-21T12:00:00Z"}
            ),
            ExtractedRelationship(
                relationship_type=RelationshipType.IN_BIOME,
                source_name="David Chen",
                target_name="Bioluminescent",
                properties={}
            )
        ],
        broadcast_info={"title": "Debug Upload", "broadcast_type": "test"}
    )
    
    print("Calling save_extraction_result...")
    try:
        stats = service.save_extraction_result(mock_result)
        print("Save Result:", stats)
        
        if stats['errors']:
            print("❌ Errors occurred:", stats['errors'])
        else:
            print("✅ Save completed without errors.")
            print(f"Created: {stats['entities_created']} entities, {stats['relationships_created']} relationships.")
            
    except Exception as e:
        print(f"❌ Exception during save: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_save()
