import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from httpx import ConnectError
from starlette.requests import Request
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

from src.classes.gdrive_fetcher import GDriveFetcher
from src.classes.gdrive_pusher import GDrivePusher
from src.models.customer import Customer
from src.models.document import Document


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the application lifespan (startup and shutdown)."""
    logging.info("Application starting up...")
    try:
        await gd_fetcher.preload()
        logging.info("Application started successfully!")
    except ConnectError as error:
        logging.error("Cant connect to GDrive!")
        return
    try:
        yield
    finally:
        logging.info("Application shutting down...")


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="src/templates")
gd_fetcher = GDriveFetcher()
gd_pusher = GDrivePusher()


@app.get("/profile/{amo_id}")
async def profile(request: Request, amo_id: int):
    customer: Customer = await gd_fetcher.get_customer(amo_id)
    context = {"request": request, "customer": customer, "amo_id": amo_id, "config": gd_fetcher.config}

    if customer is None:
        return templates.TemplateResponse("errors/404.html", context, status_code=404)

    return templates.TemplateResponse("profile.html", context)


@app.get("/")
async def say_hello(request: Request):
    context = {"request": request, "config": gd_fetcher.config}
    return templates.TemplateResponse("errors/404.html", context, status_code=404)


@app.get("/refresh")
async def refresh(request: Request):
    await gd_fetcher.preload()
    return {"status": "success"}


@app.get("/documents/{amo_id}/{doc_id}")
async def say_hello(request: Request, amo_id: int, doc_id: int):
    document: Document = await gd_fetcher.get_document(doc_id)
    context = {"request": request, "document": document, "amo_id": amo_id, "config": gd_fetcher.config}
    return templates.TemplateResponse("document.html", context)


@app.post("/upload")
async def upload_document(request: Request, file: UploadFile = File(...)):
    try:
        form_data = await request.form()
        amo_id, doc_id = int(form_data.get("amo_id")), int(form_data.get("doc_id"))

        logging.debug(f"Загружаем  {file.filename} => файл {doc_id} от пользователя {amo_id}")

        document = await gd_pusher.upload_file(file, amo_id, doc_id)
        context = {"request": request, "document": document, "amo_id": amo_id, "config": gd_fetcher.config}

        return templates.TemplateResponse("document.html", context)

    except ValueError:
        raise HTTPException(status_code=400, detail="amo_id and doc_id must be integers")
    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


if (__name__ == "__main__"):
    uvicorn.run(app, host="0.0.0.0", port=8000)
