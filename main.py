import uvicorn
from fastapi import FastAPI
from starlette.requests import Request
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="src/templates")


@app.get("/profile/{amo_id}")
async def profile(request: Request, amo_id: int):
    context = {"request": request}
    return templates.TemplateResponse("profile.html", context)


@app.get("/")
async def say_hello(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("placeholder.html", context)


if(__name__ == "__main__"):
    uvicorn.run(app, host="0.0.0.0", port=8000)
