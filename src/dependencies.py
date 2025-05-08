# Настраиваем шаблоны
from starlette.templating import Jinja2Templates

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.classes.doc_manager import DocManager
from src.classes.gas.gas_api import GDriveFetcher
from src.classes.tg.tg_logger import TGLogger
from src.utils import format_datetime_ru, markdown_to_html

templates = Jinja2Templates(directory="src/templates")
templates.env.filters["rudate"] = format_datetime_ru
templates.env.filters['markdown'] = markdown_to_html

# Создаем адаптеры для гугл-доков
gas_api = GDriveFetcher()
gd_pusher = DocManager()

tg_logger: TGLogger = TGLogger(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
