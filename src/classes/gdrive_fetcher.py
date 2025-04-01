from copy import copy
from pprint import pprint
from typing import Dict, Any

import httpx

from config import CUSTOMERS_URL, SPECIALITIES_URL, DOCUMENTS_URL
from src.models.customer import Customer
from src.models.document import Document
from src.models.speciality import Speciality

class GDriveFetcher(object):

    def __init__(self):

        self.client = httpx.AsyncClient(timeout=15.0)

        # Кешируем данные

        self.specialities: dict[int, Speciality] = {}
        self.documents: dict[int, Document] = {}
        self.customers: dict[int, Customer] = {}

    async def preload(self):
        print("caching specialities")
        self.specialities = await self.get_all_specialties()
        print("caching documents")
        self.documents = await self.get_all_documents()
        # print("caching customers")
        # self.customers = await self.get_all_customers()

    async def get_all_customers(self) -> dict[Any, Customer]:
        response = await self.client.get(CUSTOMERS_URL)
        data = response.json()
        customers = {cust.amo_id : Customer(**cust) for cust in data}
        return customers

    async def get_customer(self, amo_id) -> Customer:

        # if self.customers.get(amo_id) is not None:
        #     return self.customers.get(amo_id)

        response = await self.client.get(f"{CUSTOMERS_URL}/{amo_id}", follow_redirects=True)

        data = response.json()
        customer: Customer = Customer(**data)

        for doc_id in customer.docs_required:

            if(doc_id not in self.documents):
                raise ValueError(f"Required for customer {amo_id} document: {doc_id} was not found")

            customer.docs[doc_id] = copy(self.documents[doc_id])
            if doc_id in customer.docs_ready:
                customer.docs[doc_id].is_uploaded = True

        return customer

    async def get_all_specialties(self) -> dict[int, Speciality]:

        response = await self.client.get(SPECIALITIES_URL, follow_redirects=True)
        data = response.json()
        specialities = {spec_data["id"]: Speciality(**spec_data) for spec_data in data}
        return specialities

    async def get_all_documents(self) -> dict[int, Document]:

        response = await self.client.get(DOCUMENTS_URL, follow_redirects=True)
        data = response.json()
        documents = {doc_data["id"]: Document(**doc_data) for doc_data in data}
        return documents

    async def get_document(self, doc_id):
        pprint(self.documents)
        if self.documents.get(doc_id) is not None:
            return self.documents.get(doc_id)



