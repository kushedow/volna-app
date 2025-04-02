import base64
import logging
import os
from contextlib import asynccontextmanager
from pprint import pprint

import aiofiles
import httpx
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from httpx import ConnectError
from starlette.requests import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import JSONResponse, HTMLResponse
from starlette.staticfiles import StaticFiles

from config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER, UPLOAD_URL
from src.classes.gdrive_fetcher import GDriveFetcher
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
    # Shutdown code here (e.g., close database connection)


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", app)

templates = Jinja2Templates(directory="src/templates")
gd_fetcher = GDriveFetcher()


@app.get("/profile/{amo_id}")
async def profile(request: Request, amo_id: int):
    customer: Customer = await gd_fetcher.get_customer(amo_id)
    context = {"request": request, "customer": customer}

    if customer is None:
        return templates.TemplateResponse("errors/404.html", context, status_code=404)

    return templates.TemplateResponse("profile.html", context)


@app.get("/")
async def say_hello(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("errors/404.html", context, status_code=404)


@app.get("/documents/{amo_id}/{doc_id}")
async def say_hello(request: Request, amo_id: int, doc_id: int):
    document: Document = await gd_fetcher.get_document(doc_id)
    context = {"request": request, "document": document, "amo_id": amo_id}
    return templates.TemplateResponse("document.html", context)


@app.post("/upload")
async def upload_document(request: Request, file: UploadFile = File(...)):
    try:
        form_data = await request.form()
        amo_id = int(form_data.get("amo_id"))
        doc_id = int(form_data.get("doc_id"))

        filename = file.filename
        if not filename.lower().split(".")[-1] in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid file type: Only PDF files are allowed")

        contents = await file.read()

        file = base64.b64encode(contents).decode('utf-8')
        data = {"amo_id": amo_id, "doc_id": doc_id, "file": file}

        client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
        response = await client.post(UPLOAD_URL, data=data)
        pprint(response.json())

        document: Document = await gd_fetcher.get_document(doc_id)
        document.is_uploaded = True

        context = {"request": request, "document": document, "amo_id": amo_id}
        return templates.TemplateResponse("document.html", context)

    except ValueError:
        raise HTTPException(status_code=400, detail="amo_id and doc_id must be integers")
    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions to maintain status codes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


if (__name__ == "__main__"):
    uvicorn.run(app, host="0.0.0.0", port=8000)
