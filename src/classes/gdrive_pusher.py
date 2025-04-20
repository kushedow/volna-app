import base64
import os
from typing import Coroutine, Dict

import aiofiles
import httpx
from fastapi import HTTPException, UploadFile
from httpx import Response
from typing_extensions import TypedDict

from config import ALLOWED_EXTENSIONS, UPLOAD_URL, UPLOAD_FOLDER, logger
from src.models.document import Document, UploadedDocument
import fitz

class GasUploadedDocDict(TypedDict):
    id: int
    customer_id: int
    doc_id: int
    gdrive_id: str
    created_at: str

    title: str
    description: str
    guide: str


class GDrivePusher:

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def _send_to_gdrive(self, data) -> GasUploadedDocDict:
        """
        Отправляет данные (включая файл) на сервер Google Apps Script (GAS) для сохранения в Google Drive.
        :param data:  Словарь (dict) с данными, которые необходимо отправить на сервер GAS.
            - 'file': Закодированная в Base64 строка, представляющая содержимое файла (UploadFile).
            - 'amo_id': ID пользователя AmoCRM (int).
            - 'doc_id': ID документа (int).
        :return:
        """

        amo_id = data.get("amo_id")
        logger.info("Загрузка: Отправляем файл пользователя {amo_id} на GAS сервер", amo_id=amo_id)

        response: Response = await (self.client.post(UPLOAD_URL, data=data))
        response_data: GasUploadedDocDict = response.json()

        if "error" in response_data:
            logger.info("Загрузка: APPS SCRIPTS Сервер вернул ошибку {error} ", error= response_data["error"]["message"])
            raise HTTPException(status_code=400, detail=response_data["error"])

        logger.info("Загрузка: Файл пользователя {amo_id} загружен на GAS сервер", amo_id=amo_id)
        return response_data

    @staticmethod
    async def _save_pdf_picture(file_contents: bytes, file_name: str) -> str:
        """Сохраняет PDF (конвертируя его в PNG) в UPLOAD_FOLDER."""
        #TODO add exception handler

        logger.info("Загрузка: Создаем превью пдф файла {file_name} локально", file_name=file_name)
        pdf_document = fitz.open(stream=file_contents, filetype="pdf")
        page = pdf_document[0]
        pix = page.get_pixmap()
        img_byte_arr: bytes = pix.tobytes("png")

        image_path: str = os.path.join(UPLOAD_FOLDER, file_name)

        async with aiofiles.open(image_path, "wb") as f:
            await f.write(img_byte_arr)

        pdf_document.close()
        logger.info(f"Загрузка: Превью {file_name}  PDF сохранено: {image_path}", file_name=file_name)

        return image_path

    async def upload_file(self, file: UploadFile, amo_id: int, doc_id: int) -> UploadedDocument:
        """Загружает файл на сервер Google Drive, предварительно проверив тип файла и создав превью."""
        filename: str = file.filename

        if not filename.lower().split(".")[-1] in ALLOWED_EXTENSIONS:
            logger.warning(f"Тип файла {filename} не поддерживается. Разрешены только PDF.")
            raise HTTPException(status_code=400, detail=f"Invalid file type {filename}: Only PDF files are allowed")

        # TODO Выбросить исключения при большом размере файла

        contents: bytes = await file.read()
        file: str = base64.b64encode(contents).decode('utf-8')
        logger.debug("Загрузка: Размер файла {name} = {size}", name=filename, size= f"{len(contents) // 1024} кб")

        data = {"amo_id": amo_id, "doc_id": doc_id, "file": file}

        # TODO Проверить размер файла
        # TODO Перехватить исключения при загрузке файла

        response_data: dict = await self._send_to_gdrive(data)
        uploaded_document = UploadedDocument(**response_data)

        picture_url = await self._save_pdf_picture(contents, f"{uploaded_document.gdrive_id}.png")
        uploaded_document.picture_url = picture_url

        return uploaded_document
