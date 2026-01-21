import json
import logging
import os
from PIL import Image
from google import genai
from google.genai import types
from .base_extractor import (
    BaseExtractor, ExtractionResult, ExtractedEntity,
    ExtractedRelationship, EntityType, RelationshipType
)
from services.gcs_service import GCSService
from config import settings

logger = logging.getLogger(__name__)

class ImageExtractor(BaseExtractor):
    """Extract survivor network entities from images"""
    
    def __init__(self):
        self.client = genai.Client(
            vertexai=True, 
            project=settings.PROJECT_ID, 
            location=settings.LOCATION
        )
        self.model_name = 'gemini-2.5-flash'
        self.gcs_service = GCSService()
    
    def _get_extraction_prompt(self) -> str:
        return """Analyze this image for a Survivor Network emergency response system.

## Look for and identify:

1. **Survivors/People**: 
   - Count, apparent condition, roles (medic, leader, etc.)
   - Any visible name tags, callsigns, or identifiers

2. **Resources**:
   - Food, water, medical supplies, tools, vehicles, shelter materials
   - Estimate quantities and condition

3. **Environment/Biome**:
   - Location type (urban, forest, desert, coastal, mountain, etc.)
   - Weather, hazards, quadrant if visible (NE/NW/SE/SW)

4. **Needs apparent**:
   - Medical attention, shelter, food/water, rescue
   - Urgency level

5. **Skills being demonstrated**:
   - Medical care, construction, navigation, communication, etc.

6. **Any visible text**:
   - Signs, messages, coordinates, warnings

## Return JSON (no markdown):
{
    "summary": "Description of the scene",
    "scene_type": "camp|rescue|supply_depot|hazard|medical|shelter|other",
    "urgency_level": "critical|high|medium|low",
    "entities": [
        {
            "entity_type": "Survivor|Skill|Need|Resource|Biome",
            "name": "descriptive name",
            "properties": {
                "description": "what you see",
                "condition": "good|fair|poor",
                "quantity": "number if applicable"
            },
            "confidence": 0.0-1.0
        }
    ],
    "relationships": [
        {
            "relationship_type": "SurvivorHasSkill|SurvivorHasNeed|SurvivorFoundResource|SurvivorInBiome|SkillTreatsNeed",
            "source": "source entity name",
            "target": "target entity name",
            "properties": {},
            "confidence": 0.0-1.0
        }
    ],
    "broadcast_info": {
        "title": "suggested title",
        "broadcast_type": "report|alert|request|update"
    },
    "location_hints": ["any location clues"]
}"""

    async def extract(self, gcs_uri: str, **kwargs) -> ExtractionResult:
        """Extract entities from image"""
        temp_path = None
        try:
            # Download image
            temp_path = self.gcs_service.download_to_temp(gcs_uri)
            image = Image.open(temp_path)
            
            # Analyze with Gemini Vision
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    self._get_extraction_prompt(),
                    image
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            try:
                result_json = json.loads(response.text)
            except json.JSONDecodeError:
                # Fallback
                text = response.text.strip()
                if text.startswith('```json'):
                    text = text[7:-3]
                elif text.startswith('```'):
                    text = text[3:-3]
                result_json = json.loads(text)
            
            # Convert entities
            entities = []
            for e in result_json.get('entities', []):
                try:
                    entities.append(ExtractedEntity(
                        entity_type=EntityType(e['entity_type']),
                        name=e['name'],
                        properties=e.get('properties', {}),
                        confidence=e.get('confidence', 0.8)
                    ))
                except (ValueError, KeyError):
                    continue
            
            # Convert relationships
            relationships = []
            for r in result_json.get('relationships', []):
                try:
                    relationships.append(ExtractedRelationship(
                        relationship_type=RelationshipType(r['relationship_type']),
                        source_name=r['source'],
                        target_name=r['target'],
                        properties=r.get('properties', {}),
                        confidence=r.get('confidence', 0.8)
                    ))
                except (ValueError, KeyError):
                    continue
            
            return ExtractionResult(
                media_uri=gcs_uri,
                media_type="image",
                entities=entities,
                relationships=relationships,
                summary=result_json.get('summary', ''),
                broadcast_info=result_json.get('broadcast_info'),
                metadata={
                    'scene_type': result_json.get('scene_type'),
                    'urgency_level': result_json.get('urgency_level'),
                    'location_hints': result_json.get('location_hints', []),
                    'image_size': f"{image.width}x{image.height}"
                }
            )
            
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            raise
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
