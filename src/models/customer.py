from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.models.document import Document
from src.models.faq import FAQ
from src.models.group import Group
from src.models.speciality import Speciality


class DocStage(Enum):
    docs_collecting = "docs_collecting"
    docs_validating = "docs_validating"
    docs_submitting = "docs_submitting"
    docs_dha_received = "docs_dha_received"
    dha_review = "dha_review"
    dha_approved = "dha_approved"
    get_register_submitting = "get_register_submitting"
    get_register_review = "get_register_review"
    get_register_approved = "get_register_approved"
    completed = "completed"


class Customer(BaseModel):
    amo_id: int
    first_name: str
    full_name: str

    specialty_id: int
    specialty: Speciality = Field(default=None)

    docs_required: list[int] = Field(default_factory=list)
    docs_extra: list[str] = Field(default_factory=list)  # Provide a default value (empty list)
    docs_ready: list[int]
    docs_status: DocStage = DocStage.docs_collecting

    docs: dict[int, Document] = Field(default_factory=dict, description="Обработанный список документов")
    faq: list[FAQ] = Field(default_factory=list, description="Список FAQ доступный пользователю")

    group_id: str = Field(default=None, description="Указатель на группу")
    group: Optional[Group] = Field(default=None, description="Объект группы с куратором, преподом и экспертом")

    notification_text: str = Field(default="")

    exam_status: str = Field(default="not_scheduled")
    exam_info: str = Field(default="", description="Информация про экзамен'")
    access_info: str = Field(default="", description="Информация про доступ")

    folder_id: str

    is_activated: bool = Field(default=False, description="Активировался ли уже пользователь")

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
        return len(self.docs)
