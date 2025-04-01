import logging
from contextlib import asynccontextmanager
from pprint import pprint

import uvicorn
from fastapi import FastAPI
from httpx import ConnectError
from starlette.requests import Request
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

from src.classes.gdrive_fetcher import GDriveFetcher
from src.models.customer import Customer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the application lifespan (startup and shutdown)."""

    logging.info("Application starting up...")

    try:

        await gd_fetcher.preload()
        logging.info("Application started successfully!")
    except (ConnectError) as error:
        logging.error("Cant connect to GDrive!")
        return

    try:
        yield
    finally:
        logging.info("Application shutting down...")

    # Shutdown code here (e.g., close database connection)


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="src/templates")

gd_fetcher = GDriveFetcher()



@app.get("/profile/{amo_id}")
async def profile(request: Request, amo_id: int):
    customer: Customer = await gd_fetcher.get_customer(amo_id)
    context = {"request": request, "customer": customer}
    pprint(context)
    return templates.TemplateResponse("profile.html", context)

@app.get("/")
async def say_hello(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("placeholder.html", context)


if(__name__ == "__main__"):
    uvicorn.run(app, host="0.0.0.0", port=8000)
