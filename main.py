import locale
from contextlib import asynccontextmanager
from pprint import pprint

import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from httpx import ConnectError
from pydantic import ValidationError
from starlette.requests import Request
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

from src.classes.amo.types import ExtraDoc
from src.classes.amo_fetcher import AMOFetcher
from src.classes.gdrive_fetcher import GDriveFetcher
from src.classes.doc_manager import DocManager
from src.exceptions import InsufficientDataError
from src.models.customer import Customer
from src.models.document import Document, UploadedDocument
from src.models.group import Group
from src.models.faq import FAQ
from src.utils import format_datetime_ru, markdown_to_html

from config import logger, amo_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the application lifespan (startup and shutdown)."""
    logger.info("Запуск: Application starting up...")
    try:
        await gd_fetcher.preload()
        await amo_fetcher.preload()
        logger.info("Запуск: Application started successfully!")
    except ConnectError as error:
        logger.error("Запуск: Cant connect to GDrive!")
        return
    try:
        yield
    finally:
        logger.info("Application shutting down...")


app = FastAPI(lifespan=lifespan)

# Делаем доступными папки загрузки и статики
# Папка с загрузками должна быть смонтирована на диск как хранилище, если используется serverless
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Настраиваем шаблоны
templates = Jinja2Templates(directory="src/templates")
templates.env.filters["rudate"] = format_datetime_ru
templates.env.filters['markdown'] = markdown_to_html

# Создаем адаптеры для гугл-доков
gd_fetcher = GDriveFetcher()
amo_fetcher = AMOFetcher()
gd_pusher = DocManager()


@app.get("/lk/{amo_id}")
@app.get("/profile/{amo_id}")
async def profile(request: Request, amo_id: int):
    customer: Customer = await amo_api.fetch_lead_data(amo_id)

    context = {"request": request, "customer": customer, "amo_id": amo_id, "config": gd_fetcher.config}

    if customer is None:
        return templates.TemplateResponse("errors/404.html", context, status_code=404)

    customer.faq = gd_fetcher.faq
    customer.group = gd_fetcher.get_group(customer.group_id)
    customer.specialty = gd_fetcher.get_specialty(customer.specialty_id)

    specialty_docs = customer.specialty.docs_required
    customer.docs = gd_fetcher.get_documents_by_indices(specialty_docs, customer.docs_ready)

    # TODO добавить информацию по реально загруженным докам

    pprint(customer.docs)

    return templates.TemplateResponse("pages/profile.html", context)


@app.get("/")
async def say_hello(request: Request):
    context = {"request": request, "config": gd_fetcher.config}
    return templates.TemplateResponse("errors/404.html", context, status_code=404)


@app.get("/refresh")
async def refresh(request: Request):
    await gd_fetcher.preload()
    return {"status": "success"}


@app.get("/documents/{amo_id}/{doc_id}")
async def documents(request: Request, amo_id: int, doc_id: int):
    document: Document = gd_fetcher.get_document(doc_id)
    uploads = await gd_fetcher.get_document_uploads(amo_id, doc_id)

    context = {
        "request": request,
        "document": document,
        "uploads": uploads,
        "amo_id": amo_id,
        "config": gd_fetcher.config
    }

    return templates.TemplateResponse("pages/document.html", context)


@app.get("/documents/{amo_id}/extra/{extra_title}")
async def extra_documents(request: Request, amo_id: int, extra_title: str):

    customer: Customer = await amo_api.fetch_lead_data(amo_id)
    document: ExtraDoc | None = customer.docs_extra.get(extra_title)

    if document is None:
        raise KeyError("Документ не найден")

    uploads: list[UploadedDocument] = await gd_fetcher.get_document_uploads(amo_id, extra_title)

    context = {
        "request": request,
        "document": document,
        "uploads": uploads,
        "customer": customer,
        "amo_id": amo_id,
        "config": gd_fetcher.config
    }

    return templates.TemplateResponse("pages/document.html", context)


@app.get("/events/{amo_id}")
async def events(request: Request, amo_id: int):
    customer: Customer = await amo_api.fetch_lead_data(amo_id)
    group: Group = gd_fetcher.get_group(customer.group_id)

    context = {
        "request": request,
        "group": group,
        "amo_id": amo_id,
        "config": gd_fetcher.config
    }

    return templates.TemplateResponse("pages/events.html", context)


@app.get("/faq/{amo_id}")
async def events(request: Request, amo_id: int):
    faq: list[FAQ] = await gd_fetcher.get_all_faqs()

    context = {
        "request": request,
        "faq": faq,
        "amo_id": amo_id,
        "config": gd_fetcher.config
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

        if doc_is_extra:
            document: ExtraDoc = customer.docs_extra.get(doc_id)
            uploads = await gd_fetcher.get_document_uploads(amo_id, doc_id)
        else:
            document: Document = gd_fetcher.get_document(doc_id)
            uploads = await gd_fetcher.get_document_uploads(amo_id, doc_id)

        context = {
            "request": request,
            "document": document,
            "amo_id": amo_id,
            "config": gd_fetcher.config,
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


@app.exception_handler(InsufficientDataError)
async def unicorn_exception_handler(request: Request, exc: InsufficientDataError):
    context = {"request": request, "message": exc.message, "config": gd_fetcher.config}
    return templates.TemplateResponse("errors/400.html", context, status_code=400)


@app.exception_handler(Exception)
@app.exception_handler(ValidationError)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handles any uncaught exception, returning a generic 500 error page."""

    logger.error(f"Unhandled exception for request {request.url}: {exc}", exc_info=True)

    context = {
        "request": request,
        "config": gd_fetcher.config,
        "error_message": exc
    }

    return templates.TemplateResponse("errors/500.html", context, status_code=500)


if (__name__ == "__main__"):
    uvicorn.run(app, host="0.0.0.0", port=8001)
