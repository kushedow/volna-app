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
from src.routes.admin import admin_router
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
app.include_router(admin_router)

app.add_exception_handler(InsufficientDataError, insufficient_data_exception_handler)
app.add_exception_handler(ValidationError, generic_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Делаем доступными папки загрузки и статики
# Папка с загрузками должна быть смонтирована на диск как хранилище, если используется serverless
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/lk/{amo_id}")
@app.get("/profile/{amo_id}")
async def profile(request: Request, amo_id: int):
    """Вывод главной страницы с профилем"""
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


if (__name__ == "__main__"):
    uvicorn.run(app, host="0.0.0.0", port=8001)
