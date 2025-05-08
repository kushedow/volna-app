from starlette.requests import Request
from config import logger
from src.dependencies import templates
from src.exceptions import InsufficientDataError


async def insufficient_data_exception_handler(request: Request, exc: InsufficientDataError):
    context = {"request": request, "message": exc.message, }
    return templates.TemplateResponse("errors/400.html", context, status_code=400)


async def generic_exception_handler(request: Request, exc: Exception):
    """Handles any uncaught exception, returning a generic 500 error page."""

    logger.error(f"Unhandled exception for request {request.url}: {exc}", exc_info=True)

    context = {
        "request": request,
        "error_message": exc
    }

    return templates.TemplateResponse("errors/500.html", context, status_code=500)
