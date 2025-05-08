from fastapi import APIRouter
from starlette.requests import Request

from src.dependencies import gas_api, templates, tg_logger
admin_router = APIRouter()


@admin_router.get("/refresh")
async def refresh(request: Request):
    result = await gas_api.preload()
    context = {"request": request, "config": gas_api.config}
    await tg_logger.send_message("Данные на сервере обновлены из гугл-диска")
    return templates.TemplateResponse("admin/refreshed.html", context)
