import logging
from copy import copy
from typing import Any

import httpx

from config import CUSTOMERS_URL, SPECIALITIES_URL, DOCUMENTS_URL, FAQ_URL, GROUPS_URL, EVENTS_URL, CONFIG_URL
from src.models.customer import Customer
from src.models.document import Document, UploadedDocument
from src.models.faq import FAQ
from src.models.group import Group, Person, GroupEvent
from src.models.speciality import Speciality


class GDriveFetcher(object):

    def __init__(self):

        self.client = httpx.AsyncClient(timeout=15.0)

        # Данные , которые будут закешированы

        self.specialities: dict[int, Speciality] = {}
        self.documents: dict[int, Document] = {}
        self.customers: dict[int, Customer] = {}
        self.groups: dict[int, Group] = {}
        self.faq: list[FAQ] = []
        self.config: dict[str, str] = {}

    async def preload(self):

        print("caching config")
        self.config = await self.get_all_config()
        print("caching specialities")
        self.specialities = await self.get_all_specialties()
        print("caching documents")
        self.documents = await self.get_all_documents()
        print("caching faq")
        self.faq = await self.get_all_faqs()
        print("caching groups and its events")
        self.groups = await self.get_all_groups()

    # async def get_all_customers(self) -> dict[Any, Customer]:
    #     response = await self.client.get(CUSTOMERS_URL)
    #     data = response.json()
    #     customers = {cust.amo_id: Customer(**cust) for cust in data}
    #     return customers

    # async def get_customer(self, amo_id) -> Customer | None:
    #
    #     response = await self.client.get(f"{CUSTOMERS_URL}/{amo_id}", follow_redirects=True)
    #     data = response.json()
    #
    #     if data.get("error"):
    #         logging.debug(data)
    #         return None
    #
    #     customer: Customer = Customer(**data)
    #
    #     for doc_id in (customer.docs_required + customer.docs_extra):
    #
    #         if (doc_id not in self.documents):
    #             raise ValueError(f"Required for customer {amo_id} document: {doc_id} was not found")
    #
    #         customer.docs[doc_id] = copy(self.documents[doc_id])
    #         if doc_id in customer.docs_ready:
    #             customer.docs[doc_id].is_uploaded = True
    #
    #     # Отдаем пользователю все вопросы
    #     customer.faq = self.faq
    #     # Догружаем пользователю информацию о его группе
    #     customer.group = self.groups.get(customer.group_id)
    #
    #     return customer

    async def get_document_uploads(self, amo_id, doc_id) -> list[UploadedDocument]:
        response = await self.client.get(f"{CUSTOMERS_URL}/{amo_id}/{doc_id}", follow_redirects=True)
        docs_data = response.json()
        return [UploadedDocument(**doc) for doc in docs_data]

    async def get_all_faqs(self) -> list[FAQ]:

        response = await self.client.get(FAQ_URL, follow_redirects=True)
        faq_data = response.json()
        faq: list[FAQ] = [FAQ(**faq_item) for faq_item in faq_data]
        return faq

    # СПЕЦИАЛЬНОСТИ

    async def get_all_specialties(self) -> dict[int, Speciality]:

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

            if groups[group_id]:
                groups[group_id].events.append(GroupEvent(**event))
            else:
                logging.warn(f"Не надена группа {group_id}")

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
        response = await self.client.get(CONFIG_URL, follow_redirects=True)
        data = response.json()
        config = {conf_data["key"]: conf_data["value"] for conf_data in data}
        return config
