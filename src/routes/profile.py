from fastapi import APIRouter
from starlette.requests import Request

from config import amo_api
from src.dependencies import templates, gas_api
from src.models.customer import Customer
from src.models.document import UploadedDocument

profile_router = APIRouter()


@profile_router.get("/lk/{amo_id}")
@profile_router.get("/profile/{amo_id}")
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
