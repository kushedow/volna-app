import base64
import logging
import os

import aiofiles
import httpx
from fastapi import HTTPException, UploadFile

from config import ALLOWED_EXTENSIONS, UPLOAD_URL, UPLOAD_FOLDER
from src.models.document import Document
import fitz  # Import PyMuPDF


class GDrivePusher:

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def _send_to_gdrive(self, data):

        response = await (self.client.post(UPLOAD_URL, data=data))
        response_data = response.json()

        if "error" in response_data:  # Fixing misleading 200 status code
            raise HTTPException(status_code=400, detail=response_data["error"])

        return response_data

    async def _save_pdf_picture(self, file_contents: bytes, file_name: str):



        pdf_document = fitz.open(stream=file_contents, filetype="pdf")
        page = pdf_document[0]
        pix = page.get_pixmap()
        img_byte_arr: bytes = pix.tobytes("png")

        image_path: str = os.path.join(UPLOAD_FOLDER, file_name)

        async with aiofiles.open(image_path, "wb") as f:
            await f.write(img_byte_arr)

        pdf_document.close()  # Close the PDF document
        logging.info(f"PDF preview saved to: {image_path}")

        return image_path

    async def upload_file(self, file: UploadFile, amo_id: int, doc_id: int) -> Document:

        filename: str = file.filename

        if not filename.lower().split(".")[-1] in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid file type: Only PDF files are allowed")

        contents: bytes = await file.read()

        file: str = base64.b64encode(contents).decode('utf-8')
        data = {"amo_id": amo_id, "doc_id": doc_id, "file": file}

        response_data: dict = await self._send_to_gdrive(data)
        document = Document(**response_data)
        document.is_uploaded = True

        picture_url = await self._save_pdf_picture(contents, f"client_{amo_id}_doc_{doc_id}.png")
        document.picture_url = picture_url

        return document
