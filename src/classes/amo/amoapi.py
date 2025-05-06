import json
import zoneinfo
from datetime import datetime, timezone
from pprint import pprint
import re

import httpx
from loguru import logger
from typing_extensions import deprecated

from src.classes.amo.types import AmoCustomField, AmoBasicField, ContactDict, CustomFieldDict, ExtraDoc
from src.exceptions import InsufficientDataError
from src.models.customer import Customer


class FieldConverter:
    """
    Набор функций преобразования значений для вытаскивания из полей Амо данных в любом заданном виде
    """

    @staticmethod
    def str_to_docdict(field: AmoCustomField | AmoBasicField, lines: str, default=None) -> dict[str, ExtraDoc]:
        """
        Converting lines like: [Doc_name_1] Doc_about_1 \n [Doc_name_2] Doc_about_2
        to structure like [{name:"Doc_name_1", description: "Doc_about_1"}, {name:"Doc_name_2", description: "Doc_about_2"}]
        :return:
        """
        doc_dict: dict[str, dict] = {}
        pattern = re.compile(r"^\s*\[([^\]]+)\]\s*(.*?)\s*$")

        for line in lines.strip().split('\n'):
            line = line.strip()  # Clean up individual line whitespace
            if not line:  # Skip empty lines
                continue

            match = pattern.match(line)
            if match:
                doc_name = match.group(1).strip()
                doc_description = match.group(2).strip()
                doc_dict[doc_name] = {"id": doc_name, "title": doc_name, "description": doc_description, "is_uploaded": False}
            else:
                # Log lines that don't match the expected format
                logger.warning(f"Field {field.key if field else 'unknown'}: Line did not match expected format '[Name] Description': '{line}'")

        return doc_dict

    @staticmethod
    def timestamp_to_datetime(field: AmoCustomField | AmoBasicField, timestamp: int | str) -> datetime:
        logger.debug(timestamp)
        asian_plus_3_tz = zoneinfo.ZoneInfo("Asia/Qatar")
        return datetime.fromtimestamp(int(timestamp), tz=asian_plus_3_tz)

    @staticmethod
    def list_to_int_list(field: AmoCustomField | AmoBasicField, elements: list, default=None):
        "Выделить числа из "
        return [int(element.split()[0]) for element in elements]

    @staticmethod
    def list_first_element(field: AmoCustomField | AmoBasicField, elements: list, default=None):
        """Чтобы получить первый элемент из списка"""
        if len(elements) == 0:
            return default
        return elements[0]

    @staticmethod
    def list_first_number(field: AmoCustomField | AmoBasicField, elements: list, default=""):
        if len(elements) == 0:
            return default
        return int(elements[0].split()[0])

    @staticmethod
    def str_first_element(field: AmoCustomField | AmoBasicField, string: str, default=""):
        if len(string) == 0:
            return default
        return string.split(" ")[0]

    @staticmethod
    def str_to_list(field: AmoCustomField | AmoBasicField, string: str):
        try:
            result = json.loads(string)
        except json.decoder.JSONDecodeError as error:
            logger.error(error)
            return []
        return  result


class AmoAPI:

    def __init__(self, base_url: str, access_token: str):

        self.base_url: str = base_url
        self.access_token: str = access_token
        self.basic_fields: dict[str, AmoBasicField] = {}
        self.custom_fields: dict[str, AmoCustomField] = {}

        self.client = httpx.AsyncClient(timeout=15.0)

    # Интерфейс регистрации полей

    def add_basic_field(self, field_key, field_type, field_label, default=None):
        self.basic_fields[field_key] = AmoBasicField(field_key, field_type, field_label, default)

    def add_custom_field(self, field_key, field_id, field_type, field_label, default=None, convert: callable = None):
        """Add field to extract after fetching"""
        self.custom_fields[field_key] = AmoCustomField(field_key, field_id, field_type, field_label, default, convert)

    # Интерфейс сохранения полей

    def update_custom_field(self, key, value):
        pass

    # Необходимые для запроса заголовки

    @property
    def headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    # Загружаем данные

    async def fetch_lead_data(self, lead_id: int) -> Customer | None:

        print(lead_id)

        url = f"{self.base_url}/api/v4/leads/{lead_id}?with=contacts,status"
        response = await self.client.get(url, headers=self.headers)

        if response.status_code != 200:
            print(response)
            raise InsufficientDataError("Клиент не найден в базе")

        lead_raw = response.json()

        basic_fields: dict[str: any] = self._extract_all_basic_fields(lead_raw)
        custom_fields: dict[str: any] = self._extract_all_custom_fields(lead_raw)
        name_fields: dict[str: str] = await self._get_lead_names(lead_raw)

        customer_data: dict[str: any] = basic_fields | custom_fields | name_fields | {"amo_id": lead_id}
        print()
        print()
        pprint(customer_data)
        print()
        print()
        customer: Customer = Customer(**customer_data)

        return customer

    async def _get_lead_names(self, lead_raw) -> dict[str, str]:

        try:
            contact_id = lead_raw["_embedded"]["contacts"][0]["id"]
        except (IndexError, KeyError):
            logger.error("Не получилось получить имя")
            return {"first_name": "", "last_name": "", "full_name": ""}

        url = f"{self.base_url}/api/v4/contacts/{contact_id}?with=contacts,status"
        response = await self.client.get(url, headers=self.headers)
        if response.status_code != 200:
            logger.debug(f"Не удалось получить имя клиента {lead_raw["id"]} ")
            return {"first_name": "", "last_name": "", "full_name": ""}

        contact_raw: ContactDict = response.json()

        return {"first_name": contact_raw["first_name"], "last_name": contact_raw["last_name"], "full_name": contact_raw["name"]}

    @deprecated("Валидация вынесена из логики АМО")
    def __validate_lead_data(self, lead_data):

        if not lead_data["specialty_id"]:
            raise InsufficientDataError("Не указана информация про программу обучения")

        if not lead_data["is_activated"]:
            raise InsufficientDataError("Кабинет еще не активирован")

        return True

    def _extract_all_basic_fields(self, lead_raw) -> dict[str, AmoBasicField]:
        """Извлекает все данные на основе зарегистрированных кастомных полей"""

        result = {}
        for field in self.basic_fields.values():
            key = field.key
            if key in lead_raw:
                result[key] = lead_raw[key]
            else:
                result[key] = field.default

        return result

    def _extract_custom_field_data(self, field: AmoCustomField, field_data: CustomFieldDict) -> any:
        """Извлекает данные одного произвольного поля в зависимости от заданного для field типа"""

        # Если данных тупо нет – возвращаем дефолтное значение
        if field_data is None:
            return field.default

        elif field.type == str:
            result = field_data["values"][0]['value']

        elif field.type == list:
            result = [element["value"] for element in field_data["values"]]

        elif field.type == bool:
            result = field_data["values"][0]['value']

        elif field.type == datetime:
            result = field_data["values"][0]['value']

        else:
            result = field_data

        # Если задано правило конвертации
        if field.convert is not None:
            converted_result = field.convert(field, result)
            return converted_result

        return result

    def _extract_all_custom_fields(self, lead_raw) -> dict[str, AmoCustomField]:
        result = {}

        if "custom_fields_values" in lead_raw and lead_raw["custom_fields_values"] is not None:
            custom_data: list[dict] = lead_raw["custom_fields_values"]
        else:
            custom_data: list = []

        for field in self.custom_fields.values():
            field_key = field.key
            field_id = field.id

            field_data: CustomFieldDict | None = next((f for f in custom_data if f["field_id"] == field_id), None)

            result[field_key] = self._extract_custom_field_data(field, field_data)

        return result



