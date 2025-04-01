from pydantic import BaseModel, Field

from src.models.document import Document
from src.models.speciality import Speciality


class Customer(BaseModel):
    amo_id: int
    first_name: str
    full_name: str

    specialty_id: int
    specialty: Speciality = Field(default=None)

    docs_required: list[int]
    docs_extra: list[int] = Field(default_factory=list)  # Provide a default value (empty list)
    docs_ready: list[int]

    docs: dict[int, Document] = Field(default_factory=dict, description="Обработанный список документов")

    notification_text: str = Field(default="")
    exam_status: str
    folder_id: str

    @property
    def docs_is_ready(self) -> bool:
        """Returns True if docs_required == docs_ready."""
        return sorted(self.docs_required) == sorted(self.docs_ready)

    @property
    def docs_completed_count(self) -> int:
        """Returns the number of completed documents."""
        return len(self.docs_ready)

    @property
    def docs_total_count(self) -> int:
        """Returns the total number of required documents."""
        return len(self.docs_required)

