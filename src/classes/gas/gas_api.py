import asyncio
import logging
import httpx

from config import CUSTOMERS_URL, SPECIALITIES_URL, DOCUMENTS_URL, FAQ_URL, GROUPS_URL, EVENTS_URL, CONFIG_URL, logger, \
    GDRIVE_URL
from src.classes.amo.types import UploadedDocDict
from src.models.customer import Customer
from src.models.document import Document, UploadedDocument
from src.models.faq import FAQ
from src.models.group import Group, Person, GroupEvent
from src.models.speciality import Speciality


class GDriveFetcher:

    def __init__(self):

        self.client = httpx.AsyncClient(timeout=15.0)

        # Данные, которые будут закешированы

        self.specialities: dict[int, Speciality] = {}
        self.documents: dict[int, Document] = {}
        self.customers: dict[int, Customer] = {}
        self.groups: dict[int, Group] = {}
        self.faq: list[FAQ] = []
        self.config: dict[str, str] = {}

    async def preload(self):

        results = await asyncio.gather(
            self.get_all_config(),
            self.get_all_specialties(),
            self.get_all_documents(),
            self.get_all_faqs(),
            self.get_all_groups(),
            return_exceptions=False,
        )
        logger.info("All data recached")

        self.config, self.specialities, self.documents, self.faq, self.groups = results


    async def get_document_uploads(self, amo_id, doc_id) -> list[UploadedDocument]:
        response = await self.client.get(f"{CUSTOMERS_URL}/{amo_id}/{doc_id}", follow_redirects=True)
        docs_data = response.json()
        return [UploadedDocument(**doc) for doc in docs_data]


    async def get_all_uploads(self, amo_id) -> list[UploadedDocument]:

        response = await self.client.get(f"{GDRIVE_URL}/alldocs/{amo_id}", follow_redirects=True)
        docs_data: list[UploadedDocDict] = response.json()
        return [UploadedDocument(**doc) for doc in docs_data]


    async def get_all_faqs(self) -> list[FAQ]:

        response = await self.client.get(FAQ_URL, follow_redirects=True)
        faq_data = response.json()
        faq: list[FAQ] = [FAQ(**faq_item) for faq_item in faq_data]
        return faq

    # СПЕЦИАЛЬНОСТИ

    async def get_all_specialties(self) -> dict[int, Speciality]:

        logger.info("Caching specialities")
        response = await self.client.get(SPECIALITIES_URL, follow_redirects=True)
        data = response.json()
        specialities = {spec_data["id"]: Speciality(**spec_data) for spec_data in data}
        return specialities

    def get_specialty(self, specialty_id):
        """
        Возвращает специальность
        :param specialty_id:
        :return:
        """
        return self.specialities.get(specialty_id)

    # ГРУППЫ

    async def get_all_groups(self):

        logger.info("Caching groups")
        response = await self.client.get(GROUPS_URL, follow_redirects=True)
        all_groups = response.json()

        groups = {}
        for gr in all_groups:

            group_id = gr["id"]
            chat_tg = gr["chat_tg"]

            if not group_id:
                continue

            curator = Person(
                name=gr.get("curator_name"),
                role="Куратор",
                avatar=gr.get("curator_avatar"),
                description=gr.get("curator_description"),
                tg=gr.get("curator_tg"),
            )
            teacher = Person(
                name=gr.get("teacher_name"),
                role="Преподаватель",
                avatar=gr.get("teacher_avatar"),
                description=gr.get("teacher_description"),
                tg=gr.get("teacher_tg"),
            )
            expert = Person(
                name=gr.get("expert_name"),
                role="Эксперт",
                avatar=gr.get("expert_avatar"),
                description=gr.get("expert_description"),
                tg=gr.get("expert_tg"),
            )

            groups[group_id] = (Group(id=group_id, chat_tg=chat_tg, curator=curator, teacher=teacher, expert=expert))

        # Досыпаем к каждой группе ее события

        response = await self.client.get(EVENTS_URL, follow_redirects=True)
        all_events = response.json()

        for event in all_events:
            group_id = event["group_id"]

            if groups.get(group_id):
                groups[group_id].events.append(GroupEvent(**event))
            else:
                logging.warn(f"Не найдена группа {group_id}")

        return groups

    def get_group(self, group_id) -> Group | None:
        """
        Возвращает группу из закешированного списка
        """
        return self.groups.get(group_id)

    # ДОКУМЕНТЫ

    def get_document(self, doc_id):
        """
        Возвращает документ из закешированного списка документов
        """

        if self.documents.get(doc_id) is not None:
            return self.documents.get(doc_id)

    async def get_all_documents(self) -> dict[int, Document]:
        logger.info("Caching documents")
        response = await self.client.get(DOCUMENTS_URL, follow_redirects=True)
        data = response.json()
        documents = {doc_data["id"]: Document(**doc_data) for doc_data in data}
        return documents

    def get_documents_by_indices(self, indices, docs_ready) -> dict[int, Document]:
        """
        Возвращает словарь документов по индексам и отмечает загруженные
        """
        docs: dict[int, Document] = {}
        for index in indices:
            doc: Document = self.get_document(index)
            if doc.id in docs_ready:
                doc.is_uploaded = True
            docs[doc.id] = doc

        return docs

    async def get_all_config(self):
        logger.info("Caching configs")
        response = await self.client.get(CONFIG_URL, follow_redirects=True)
        data = response.json()
        config = {conf_data["key"]: conf_data["value"] for conf_data in data}
        return config
