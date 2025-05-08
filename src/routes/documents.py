from fastapi import APIRouter
from starlette.requests import Request

from src.dependencies import gas_api, templates
from src.models.document import Document

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
