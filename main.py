from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from httpx import ConnectError
from pydantic import ValidationError
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

from src.dependencies import gas_api, templates
from src.exceptions import InsufficientDataError
from src.models.customer import Customer
from src.models.group import Group
from src.models.faq import FAQ

from config import logger, amo_api
from src.routes.admin import admin_router
from src.routes.api import api_router
from src.routes.documents import document_router
from src.routes.exceptions import insufficient_data_exception_handler, generic_exception_handler
from src.routes.profile import profile_router


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

routers = (document_router, admin_router, api_router, profile_router)
for router in routers:
    app.include_router(router)


app.add_exception_handler(InsufficientDataError, insufficient_data_exception_handler)
app.add_exception_handler(ValidationError, generic_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Делаем доступными папки загрузки и статики
# Папка с загрузками должна быть смонтирована на диск как хранилище, если используется serverless
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
async def say_hello(request: Request):
    """ Вывод главной страницы, с ошибкой """
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
