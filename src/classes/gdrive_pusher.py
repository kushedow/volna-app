import base64

import httpx
from fastapi import HTTPException, UploadFile

from config import ALLOWED_EXTENSIONS, UPLOAD_URL
from src.models.document import Document


class GDrivePusher:

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)

    async def upload_file(self, file: UploadFile, amo_id, doc_id) -> Document:

        filename = file.filename

        if not filename.lower().split(".")[-1] in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid file type: Only PDF files are allowed")

        contents = await file.read()

        file = base64.b64encode(contents).decode('utf-8')
        data = {"amo_id": amo_id, "doc_id": doc_id, "file": file}

        response = await (self.client.post(UPLOAD_URL, data=data))
        response_data = response.json()

        # Fixing misleading 200 status code
        if "error" in response_data:
            raise HTTPException(status_code=400, detail=response_data["error"])

        document = Document(**response_data)
        document.is_uploaded = True

        return document



