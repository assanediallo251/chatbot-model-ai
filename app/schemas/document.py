import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str
    status: str
    chunk_count: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class UploadedDocument(BaseModel):
    document: DocumentOut
    duplicated: bool


class DocumentUploadResponse(BaseModel):
    documents: list[UploadedDocument]
    uploaded_count: int
    duplicate_count: int
