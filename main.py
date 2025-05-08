from contextlib import asynccontextmanager
from pprint import pprint

import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from httpx import ConnectError
from pydantic import ValidationError
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

from src.classes.amo.types import ExtraDoc
from src.dependencies import gas_api, templates, gd_pusher
from src.exceptions import InsufficientDataError
from src.models.customer import Customer
from src.models.document import Document, UploadedDocument
from src.models.group import Group
from src.models.faq import FAQ

from config import logger, amo_api
from src.routes.documents import document_router
from src.routes.exceptions import insufficient_data_exception_handler, generic_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the application lifespan (startup and shutdown)."""
    logger.info("Запуск: Application starting up...")
    try:
        await gas_api.preload()
        logger.info("Запуск: Application started successfully!")
    except ConnectError as error:
        logger.error("Запуск: Cant connect to GDrive!")
        return
    try:
        yield
    finally:
        logger.info("Application shutting down...")


app = FastAPI(lifespan=lifespan)

app.include_router(document_router)

app.add_exception_handler(InsufficientDataError, insufficient_data_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
app.add_exception_handler(ValidationError, generic_exception_handler)  # Assuming you want ValidationError handled generically

# Делаем доступными папки загрузки и статики
# Папка с загрузками должна быть смонтирована на диск как хранилище, если используется serverless
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/lk/{amo_id}")
@app.get("/profile/{amo_id}")
async def profile(request: Request, amo_id: int):

    customer: Customer = await amo_api.fetch_lead_data(amo_id)

    context = {"request": request, "customer": customer, "amo_id": amo_id, "config": gas_api.config}

    if customer is None:
        return templates.TemplateResponse("errors/404.html", context, status_code=404)

    customer.faq = gas_api.faq
    customer.group = gas_api.get_group(customer.group_id)
    customer.specialty = gas_api.get_specialty(customer.specialty_id)

    specialty_docs = customer.specialty.docs_required
    customer.docs = gas_api.get_documents_by_indices(specialty_docs, customer.docs_ready)

    # Досыпаем пользователю информацию про все загруженные файлы пользователя
    all_uploads: list[UploadedDocument] = await gas_api.get_all_uploads(amo_id)
    customer.set_uploads(all_uploads)

    return templates.TemplateResponse("pages/profile.html", context)


@app.get("/")
async def say_hello(request: Request):
    context = {"request": request, "config": gas_api.config}
    return templates.TemplateResponse("errors/404.html", context, status_code=404)


@app.get("/refresh")
async def refresh(request: Request):
    await gas_api.preload()
    return {"status": "success"}




@app.get("/documents/{amo_id}/extra/{extra_title}")
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


@app.get("/events/{amo_id}")
async def events(request: Request, amo_id: int):
    """Вывод странички с событиями"""
    customer: Customer = await amo_api.fetch_lead_data(amo_id)
    group: Group = gas_api.get_group(customer.group_id)

    context = {
        "request": request,
        "group": group,
        "amo_id": amo_id,
        "config": gas_api.config
    }

    return templates.TemplateResponse("pages/events.html", context)


@app.get("/faq/{amo_id}")
async def events(request: Request, amo_id: int):
    """Вывод странички FAQ"""
    faq: list[FAQ] = await gas_api.get_all_faqs()

    context = {
        "request": request,
        "faq": faq,
        "amo_id": amo_id,
        "config": gas_api.config
    }

    return templates.TemplateResponse("pages/faq.html", context)


@app.post("/upload")
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

        logger.debug(f"Загрузка:  Начинаем загрузку файла {index}")

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



if (__name__ == "__main__"):
    uvicorn.run(app, host="0.0.0.0", port=8001)
