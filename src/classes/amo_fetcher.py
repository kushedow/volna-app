import asyncio
import json
import logging
from pprint import pprint

import httpx

from config import AMO_ACCESS_TOKEN, AMO_BASE_URL
from src.exceptions import InsufficientDataError
from src.models.customer import Customer


class AMOFetcher:

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

        self.fields = {
            "group": "676687",
            "product": "673621",
        }

    @property
    def headers(self) -> dict:
        return {
            'Authorization': f'Bearer {AMO_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }

    async def get_funnel_steps(self) -> dict:
        """
        Получаем шаги воронки из Амо
        :return:
        """
        pipeline_id = 9490932

        statuses_url = f"{AMO_BASE_URL}/api/v4/leads/pipelines/{pipeline_id}/statuses"
        statuses_response = await self.client.get(statuses_url, headers=self.headers)
        result = statuses_response.json()['_embedded']['statuses']
        statuses = {item["id"]: item["name"] for item in result}
        return statuses

    @property
    def fields_keys(self) -> dict:
        """
        Кастомные поля из амо, нужные в модели пользователя
        """
        return {
            "specialty_id": 679701,
            "docs_extra": 679703,
            "docs_ready": 679697,
            "notification_text": 679713,
            "group_id": 676687,
            "exam_status": 679705,
            "exam_info": 679707,
            "folder_id": 679711,
            "is_activated": 679695,

        }

    def _extract_lead_data(self, lead_data: dict) -> dict:
        """
        Вытаскивает нужные ключи из амошных данных лида
        """
        custom_fields = lead_data["custom_fields_values"]
        custom_keys = self.fields_keys.values()
        lead_data = {}

        for field in custom_fields:
            if field["field_id"] not in custom_keys:
                continue

            field_id = field["field_id"]
            field_value = field["values"]
            field_type = field["field_type"]

            if field_type == "checkbox":
                lead_data[field_id] = field_value[0]["value"]
            if field_type in ("text", "textarea"):
                lead_data[field_id] = field_value[0]["value"]
            if field_type == "multiselect":
                lead_data[field_id] = [f["value"] for f in field_value]
            if field_type == "select":
                lead_data[field_id] = field_value[0]["value"]

        return {key: lead_data.get(id) for key, id in self.fields_keys.items()}

    async def get_lead(self, lead_id) -> Customer | None:
        """
        Получаем данные лида из Амо, возврашаем неполный объект клиента
        :param lead_id: id клиента в Amo
        :return:
        """

        url = f"{AMO_BASE_URL}/api/v4/leads/{lead_id}?with=contacts,status"
        response = await self.client.get(url, headers=self.headers)
        if response.status_code != 200:
            return None

        lead_raw = response.json()

        pprint(lead_raw)

        if lead_raw.get("custom_fields_values") is None :
            raise InsufficientDataError("Не удалось загрузить расширенные данные клиента")

        lead_data = self._extract_lead_data(lead_raw)

        if not lead_data["specialty_id"]:
            raise InsufficientDataError("Не указана информация про программу обучения")

        if not lead_data["is_activated"]:
            raise InsufficientDataError("Ваш кабинет еще не активирован")



        contact_id = lead_raw['_embedded']['contacts'][0]['id']
        lead_data["specialty_id"] = int(lead_data["specialty_id"].split()[0])

        lead_data["docs_ready"] = [ int(doc.split()[0]) for doc in lead_data["docs_ready"]]
        lead_data["docs_extra"] = [ doc.strip() for doc in lead_data["docs_extra"].split()]
        lead_data["group_id"] = lead_data["group_id"][0]
        lead_data["amo_id"] = lead_id

        contact = await self._get_contact(contact_id)
        if contact is not None:
            lead_data["first_name"] = contact["first_name"].split()[0]
            lead_data["full_name"] = contact["first_name"]

        customer = Customer(**lead_data)

        return customer

    async def _get_contact(self, contact_id) -> dict:
        """
        Получаем данные с именем клиента, так как в карточке лида его нет
        :param contact_id:
        :return:
        """
        try:
            url = f"{AMO_BASE_URL}/api/v4/contacts/{contact_id}"
            response = await self.client.get(url, headers=self.headers)
            return response.json()
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error while fetching contact {contact_id}: {e}")
            return None  # Or raise an HTTPException to prevent operation
        except httpx.RequestError as e:
            logging.error(f"Request error while fetching contact {contact_id}: {e}")
            return None  # Or raise an HTTPException
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON response for contact {contact_id}: {e}")
            return None #Or rise another type exception, or reraise.
        except Exception as e:
            logging.exception(f"Unexpected error while fetching contact {contact_id}: {e}")
            return None #Or rise HTTP exception or reraise


async def main():
    amo_fetcher = AMOFetcher()
    customer = await amo_fetcher.get_lead(17322537)
    pprint(customer)
    # statuses = await amo_fetcher.get_funnel_steps()
    # print(statuses)


asyncio.run(main())
