from fastapi import APIRouter
from starlette.requests import Request

from src.dependencies import gas_api, templates

admin_router = APIRouter()


@admin_router.get("/refresh")
async def refresh(request: Request):
    result = await gas_api.preload()
    context = {"request": request}
    return templates.TemplateResponse("admin/refreshed.html", context)
