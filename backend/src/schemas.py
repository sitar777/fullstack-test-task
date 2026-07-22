from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.config import MAX_TITLE_LENGTH, MAX_UPLOAD_SIZE_BYTES

Title = Annotated[str, Field(min_length=1, max_length=MAX_TITLE_LENGTH)]
UploadContent = Annotated[bytes, Field(min_length=1, max_length=MAX_UPLOAD_SIZE_BYTES)]


class ValidatedUpload(BaseModel):
    content: UploadContent
    filename: str
    content_type: str | None = None


class FileItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_name: str
    mime_type: str
    size: int
    processing_status: str
    scan_status: str | None
    scan_details: str | None
    metadata_json: dict | None
    requires_attention: bool
    created_at: datetime
    updated_at: datetime


class FileUpdate(BaseModel):
    title: Title


class AlertItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_id: str
    level: str
    message: str
    created_at: datetime
