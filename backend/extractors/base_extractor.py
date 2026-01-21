from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class EntityType(Enum):
    SURVIVOR = "Survivor"
    SKILL = "Skill"
    NEED = "Need"
    RESOURCE = "Resource"
    BIOME = "Biome"
    BROADCAST = "Broadcast"

class RelationshipType(Enum):
    HAS_SKILL = "SurvivorHasSkill"
    HAS_NEED = "SurvivorHasNeed"
    FOUND_RESOURCE = "SurvivorFoundResource"
    IN_BIOME = "SurvivorInBiome"
    CAN_HELP = "SurvivorCanHelp"
    TREATS = "SkillTreatsNeed"

@dataclass
class ExtractedEntity:
    """Entity extracted from media - maps to your node tables"""
    entity_type: EntityType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_type": self.entity_type.value,
            "name": self.name,
            "properties": self.properties,
            "confidence": self.confidence
        }

@dataclass
class ExtractedRelationship:
    """Relationship extracted - maps to your edge tables"""
    relationship_type: RelationshipType
    source_name: str  # Name of source entity
    target_name: str  # Name of target entity
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "relationship_type": self.relationship_type.value,
            "source": self.source_name,
            "target": self.target_name,
            "properties": self.properties,
            "confidence": self.confidence
        }

@dataclass
class ExtractionResult:
    """Complete extraction result from any media"""
    media_uri: str
    media_type: str
    entities: List[ExtractedEntity] = field(default_factory=list)
    relationships: List[ExtractedRelationship] = field(default_factory=list)
    raw_content: str = ""
    summary: str = ""
    broadcast_info: Optional[Dict[str, Any]] = None  # For creating Broadcast node
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "media_uri": self.media_uri,
            "media_type": self.media_type,
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "summary": self.summary,
            "broadcast_info": self.broadcast_info,
            "metadata": self.metadata
        }

class BaseExtractor(ABC):
    """Base class for media extractors"""
    
    @abstractmethod
    async def extract(self, gcs_uri: str, **kwargs) -> ExtractionResult:
        pass
