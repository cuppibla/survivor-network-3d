import os
import uuid
import logging
import tempfile
import mimetypes
from typing import Tuple, Optional
from google.cloud import storage
from config import settings, ExtractionConfig, MediaType

logger = logging.getLogger(__name__)

class GCSService:
    """Handle all GCS operations"""
    
    def __init__(self):
        # Initialize client with optional credentials if configured via env
        self.client = storage.Client(project=settings.PROJECT_ID)
        self.bucket = self.client.bucket(settings.GCS_BUCKET_NAME)
        self.config = ExtractionConfig()
    
    def detect_media_type(self, file_path: str) -> MediaType:
        """Detect media type from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in self.config.TEXT_EXTENSIONS:
            return MediaType.TEXT
        elif ext in self.config.IMAGE_EXTENSIONS:
            return MediaType.IMAGE
        elif ext in self.config.VIDEO_EXTENSIONS:
            return MediaType.VIDEO
        elif ext in self.config.AUDIO_EXTENSIONS:
            return MediaType.AUDIO
        else:
            # Fallback to MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                if 'text' in mime_type:
                    return MediaType.TEXT
                elif 'image' in mime_type:
                    return MediaType.IMAGE
                elif 'video' in mime_type:
                    return MediaType.VIDEO
                elif 'audio' in mime_type:
                    return MediaType.AUDIO
            return MediaType.TEXT  # Default fallback
    
    def upload_file(self, file_path: str, survivor_id: Optional[str] = None) -> Tuple[str, MediaType]:
        """Upload file to GCS, organized by media type"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        media_type = self.detect_media_type(file_path)
        
        # Create organized path: media/{type}/{survivor_id or 'unknown'}/{uuid}_{filename}
        survivor_folder = survivor_id or "unknown"
        blob_name = f"media/{media_type.value}/{survivor_folder}/{uuid.uuid4()}_{os.path.basename(file_path)}"
        
        blob = self.bucket.blob(blob_name)
        blob.upload_from_filename(file_path)
        
        gcs_uri = f"gs://{settings.GCS_BUCKET_NAME}/{blob_name}"
        logger.info(f"Uploaded {media_type.value} to {gcs_uri}")
        
        return gcs_uri, media_type
    
    def download_to_temp(self, gcs_uri: str) -> str:
        """Download file from GCS to temp location"""
        blob_name = gcs_uri.replace(f"gs://{settings.GCS_BUCKET_NAME}/", "")
        blob = self.bucket.blob(blob_name)
        
        # Get extension from blob name
        ext = os.path.splitext(blob_name)[1] or '.tmp'
        
        temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        blob.download_to_filename(temp_file.name)
        temp_file.close()
        
        return temp_file.name
    
    def read_text_content(self, gcs_uri: str) -> str:
        """Read text content directly from GCS"""
        blob_name = gcs_uri.replace(f"gs://{settings.GCS_BUCKET_NAME}/", "")
        blob = self.bucket.blob(blob_name)
        return blob.download_as_text()
