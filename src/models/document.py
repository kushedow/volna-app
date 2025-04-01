from pydantic import BaseModel, Field


class Document(BaseModel):

    id: int = Field(..., description="Unique identifier")
    title: str = Field(..., min_length=1, max_length=255, description="Title of the document")
    description: str = Field(..., description="Brief description of the document")
    guide: str = Field(..., description="Detailed guide how to get the document")

    is_uploaded: str = False
    file_id: str = Field(default=None, description="GDrive Unique identifier")
