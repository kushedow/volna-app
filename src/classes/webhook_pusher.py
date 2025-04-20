import logging
from http.client import HTTPException

import httpx

ALBATO_NOTE_WEBHOOK = "https://h.albato.ru/wh/38/1lfhppn/t1musdxlKThqewpqzrQq6y0dvj8-e3RZjbnYClo6qIw/"
ALBATO_TASK_WEBHOOK = "https://h.albato.ru/wh/38/1lfhppn/ncgbtSUJHBZQLY4mAwBnLzwlLfPqwT_BWrEzj8fiS3k/"

class WebhookPusher:

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=5.0)

    async def add_note(self, lead_id, message, JSON=None):

        try:
            date = {"amo_id": lead_id, "message": message}
            response = await self.client.post(ALBATO_NOTE_WEBHOOK, json=date)
            if response.status_code == 200:
                logging.log(f"[Albato] Отправлено сообщение для {lead_id} : {message}")
            else:
                raise HTTPException()
        except HTTPException as error:
            logging.warn(f"[Albato] Не удалось отправить сообщение для {lead_id} : {message} {JSON.dumps(error)}")

            

    async def add_task(self, lead_id, manager_id, message):
        pass



