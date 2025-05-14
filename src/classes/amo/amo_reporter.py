import httpx
from httpx import HTTPError
from loguru import logger


class AmoReporter:

    def __init__(self, report_url):
        self._report_url = report_url
        self.client = httpx.AsyncClient(timeout=15.0)

    async def activate(self, amo_id: int):
        """Отмечает в АМО, что клиент активировался"""

        event_type = "activate"
        payload = {"event_type": event_type, "deal_id": amo_id}
        result = await self._make_request(payload)
        logger.debug(result.json())
        return result.json()

    async def update_documents(self, amo_id: int, doc_ids: list[int]):
        """Отмечает в АМО новый список загруженных документов"""
        event_type = "update_documents"
        payload = {"event_type": event_type, "deal_id": amo_id, "documents": doc_ids}
        result = await self._make_request(payload)
        return result.json()

    async def add_comment(self, amo_id: int, message: str):
        """Добавляет в АМО новый комментарий"""
        event_type = "add_comment"
        payload = {"event_type": event_type, "deal_id": amo_id, "message": message}
        result = await self._make_request(payload)
        return result.json()

    async def add_task(self, amo_id: int, title: str, description: str):
        """Добавляет в АМО новую задачу"""
        event_type = "add_task"
        payload = {"event_type": event_type, "deal_id": amo_id, "title": title, "description": description}
        result = await self._make_request(payload)
        return result.json()

    async def _make_request(self, payload):
        try:
            logger.info(f"Отправляем запрос {payload["event_type"]} в AMO для пользователя {payload["amo_id"]}")
            response = await self.client.post(self._report_url, json=payload)
            return response

        except HTTPError as error:
            logger.error(f"Не удалось отправить {payload["event_type"]} в AMO для пользователя {payload["amo_id"]}")
            return {}

