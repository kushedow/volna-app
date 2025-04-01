from pydantic import BaseModel, Field

from src.models.document import Document


class Speciality(BaseModel):
    id: int
    title: str
    docs_required: list[int]
    description: str
