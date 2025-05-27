from fastapi import APIRouter

from config import amo_api
from src.models.customer import Customer

api_router = APIRouter()


@api_router.get("/api/profile/{amo_id}")
async def documents(amo_id: int):
    # Загружаем данные из AMO
    customer: Customer = await amo_api.fetch_lead_data(amo_id)
    return customer.model_dump()
