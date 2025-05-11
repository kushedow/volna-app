from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.classes.amo.types import ExtraDoc, DocStatsDict
from src.models.document import Document, UploadedDocument
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

    pipeline_id: int
    status_id: int

    specialty_id: int = Field(default=None)
    specialty: Speciality = Field(default=None)

    docs_required: list[int] = Field(default_factory=list)
    docs_extra: dict[str, Document] = Field(default_factory=dict)
    docs_ready: list[int] = Field(default_factory=list)
    docs_status: DocStage = DocStage.docs_collecting

    docs: dict[int, Document] = Field(default_factory=dict, description="Обработанный список документов")
    uploads: dict[str | int, UploadedDocument] = Field(default_factory=dict, description="Хранилище всех загруженных документов")

    faq: list[FAQ] = Field(default_factory=list, description="Список FAQ доступный пользователю")

    group_id: str = Field(default=None, description="Указатель на группу")
    group: Optional[Group] = Field(default=None, description="Объект группы с куратором, преподом и экспертом")

    notification_text: str = Field(default="")

    exam_status: str = Field(default="not_scheduled")
    exam_info: str = Field(default="", description="Информация про экзамен'")
    exam_datetime: datetime | None = Field(default="", description="Дата экзамена")

    access_info: str = Field(default="", description="Информация про доступ")

    folder_id: str = Field(default="", description="ID папки на гугл-диске")

    is_activated: bool = Field(default=False, description="Активировался ли уже пользователь")
    has_full_support: bool = Field(default=False, description="Оплачено ли сопровождение (влияет на отображение блоков)")

    def set_uploads(self, uploads: list[UploadedDocument]):
        """Sets uploaded status info for basic and extra uploads"""

        for upload in uploads:

            if upload.is_extra:  # Если дополнительный документ
                doc = self.docs_extra.get(upload.doc_id)
            else:  # Если обычный документ
                doc = self.docs.get(upload.doc_id)

            if doc is not None:
                doc.is_uploaded = True
                doc.uploads.append(upload)

    @property
    def docs_stats(self) -> DocStatsDict:

        basic_total = len(self.docs)
        basic_uploaded = sum([1 if doc.is_uploaded else 0 for doc in self.docs.values()])
        extra_total = len(self.docs_extra)
        extra_uploaded = sum([1 if doc.is_uploaded else 0 for doc in self.docs_extra.values()])

        total = basic_total + extra_total
        uploaded = basic_uploaded + extra_uploaded

        return {
            "total": total,
            "uploaded": uploaded,
            "basic_total": basic_total,
            "basic_uploaded":basic_uploaded,
            "extra_total": extra_total,
            "extra_uploaded": extra_uploaded,
        }
