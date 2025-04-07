from datetime import datetime

from pydantic import BaseModel, Field


class UploadedDocument(BaseModel):
    customer_id: int = Field(...)
    doc_id: int = Field(...)
    gdrive_id: str = Field(...)
    created_at: datetime = Field(...)
    picture_url: str = Field(default=None, description="Picture URL of the document")

class Document(BaseModel):

    id: int = Field(..., description="Unique identifier")
    title: str = Field(..., min_length=1, max_length=255, description="Title of the document")
    description: str = Field(..., description="Brief description of the document")
    guide: str = Field(..., description="Detailed guide how to get the document")

    uploads: list[UploadedDocument] = Field(default_factory=list)

    is_uploaded: bool = Field(default=False, description="Whether the document was uploaded")
    doc_id: int = Field(default=None, description="duplicates id for idk what reason xD")  #
    gdrive_id: str = Field(default=None, description="GDrive Uploaded File Unique identifier")

