from fastapi import APIRouter, File, UploadFile, HTTPException
from starlette.requests import Request
from loguru import logger

from config import amo_api
from src.classes.amo.types import ExtraDoc
from src.dependencies import gas_api, templates, gd_pusher
from src.models.customer import Customer
from src.models.document import Document, UploadedDocument

document_router = APIRouter()


@document_router.get("/documents/{amo_id}/{doc_id}")
async def documents(request: Request, amo_id: int, doc_id: int):
    document: Document = gas_api.get_document(doc_id)
    uploads = await gas_api.get_document_uploads(amo_id, doc_id)

    context = {
        "request": request,
        "document": document,
        "uploads": uploads,
        "amo_id": amo_id,
        "config": gas_api.config
    }

    return templates.TemplateResponse("pages/document.html", context)


@document_router.get("/documents/{amo_id}/extra/{extra_title}")
async def extra_documents(request: Request, amo_id: int, extra_title: str):
    customer: Customer = await amo_api.fetch_lead_data(amo_id)
    document: ExtraDoc | None = customer.docs_extra.get(extra_title)

    if document is None:
        raise KeyError("Документ не найден")

    uploads: list[UploadedDocument] = await gas_api.get_document_uploads(amo_id, extra_title)

    context = {
        "request": request,
        "document": document,
        "uploads": uploads,
        "customer": customer,
        "amo_id": amo_id,
        "config": gas_api.config
    }

    return templates.TemplateResponse("pages/document.html", context)



@document_router.post("/upload")
async def upload_documents(request: Request, file: UploadFile = File(...), file_2: UploadFile = File(...),
                           file_3: UploadFile = File(...)):
    try:
        form_data = await request.form()

        amo_id = int(form_data.get("amo_id"))
        doc_id: str = form_data.get("doc_id")
        doc_is_extra: bool = bool(form_data.get("doc_is_extra"))

        customer: Customer = await amo_api.fetch_lead_data(amo_id)

        logger.debug(f"Загрузка: {file.filename} => файл {doc_id} от пользователя {amo_id}")

        files_to_upload = filter(lambda f: f.filename, [file, file_2, file_3])
        for index, one_file in enumerate(files_to_upload, start=1):
            logger.debug(f"Загрузка:  Начинаем загрузку файла {index}")
            result = await gd_pusher.upload_file(one_file, amo_id, doc_id)

        # Смотрим, какой документ, принимаем решение в зависимости от этого

        if doc_is_extra:
            document: ExtraDoc = customer.docs_extra.get(doc_id)
            uploads = await gas_api.get_document_uploads(amo_id, doc_id)
        else:
            document: Document = gas_api.get_document(doc_id)
            uploads = await gas_api.get_document_uploads(amo_id, doc_id)

        context = {
            "request": request,
            "document": document,
            "amo_id": amo_id,
            "config": gas_api.config,
            "uploads": uploads,
            "doc_is_extra": doc_id.isalpha(),
        }

        return templates.TemplateResponse("pages/document.html", context)

    except ValueError:
        raise HTTPException(status_code=400, detail="amo_id or doc_id incorrect")
    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

