from pydantic import BaseModel, Field


class Document(BaseModel):

    id: int = Field(..., description="Unique identifier")
    title: str = Field(..., min_length=1, max_length=255, description="Title of the document")
    description: str = Field(..., description="Brief description of the document")
    guide: str = Field(..., description="Detailed guide how to get the document")

    is_uploaded: bool = Field(default=False, description="Whether the document was uploaded")
    doc_id: int = Field(default=None, description="duplicates id for idk what reason xD")  #
    gdrive_id: str = Field(default=None, description="GDrive Uploaded File Unique identifier")

    picture_url: str = Field(default=None, description="Picture URL of the document")
