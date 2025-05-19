import os
import zoneinfo
from datetime import datetime

from loguru import logger

from src.classes.amo.amoapi import AmoAPI
from src.classes.amo.amoapi import FieldConverter as FC
from src.classes.tg.tg_logger import TGLogger

# GAS CONFIGS

GDRIVE_URL = "https://script.google.com/macros/s/AKfycbwJpmxd3x3mysp53z5AYxf0xwqUYRz1VwJRAWnQyPRfjCz0dG7iJvs6p-Vk2Z1iX1GN/exec?query="

CUSTOMERS_URL = GDRIVE_URL + "/customers"
SPECIALITIES_URL = GDRIVE_URL + "/specialities"
DOCUMENTS_URL = GDRIVE_URL + "/documents"
UPLOAD_URL = GDRIVE_URL + "/upload"
FAQ_URL = GDRIVE_URL + "/faq"
GROUPS_URL = GDRIVE_URL + "/groups"
EVENTS_URL = GDRIVE_URL + "/events"
CONFIG_URL = GDRIVE_URL + "/config"

# TIMEZONE CONFIGS

TIMEZONE = zoneinfo.ZoneInfo("Asia/Qatar")

# AMO CONFIGS

AMO_BASE_URL = "https://xeniaceo.kommo.com"
AMO_ACCESS_TOKEN = os.getenv("AMO_ACCESS_TOKEN")
OPERATIONAL_FUNNEL_ID = 9490932
AMO_REPORT_URL = "https://hooks.tglk.ru/in/BJDvgNxVN9evDeC81ZU3zx7m6Gzw35"

# UPLOAD CONFIGS

ALLOWED_EXTENSIONS = ["pdf"]
UPLOAD_FOLDER = "uploads"
logger.add(UPLOAD_FOLDER + "/file_{time}.log", rotation="12:00")

# TELEGRAM CONFIGS

TELEGRAM_BOT_TOKEN=os.getenv("TG_BOT_TOKEN")
TELEGRAM_CHAT_ID=os.getenv("TG_CHAT_ID")
TELEGRAM_LOG_LEVEL="WARNING"

# Настраиваем апишку

amo_api = AmoAPI(AMO_BASE_URL, AMO_ACCESS_TOKEN)

amo_api.add_basic_field("pipeline_id", int, "ID Воронки")
amo_api.add_basic_field("status_id", int, "ID статуса")

amo_api.add_custom_field("specialty_id", 679701, list, "ID специальности", 0, FC.list_first_number)

amo_api.add_custom_field("docs_extra", 680059, str, "Экстрадоки строкой", {}, FC.str_to_docdict)
amo_api.add_custom_field("docs_ready", 679697, list, "Готовые документы", [].copy(), FC.list_to_int_list)

amo_api.add_custom_field("notification_text", 679713, str, "Уведомление для ЛК", "")
amo_api.add_custom_field("group_id", 676687, list, "ID потока", "", FC.list_first_element)

amo_api.add_custom_field("exam_status", 679705, str, "статус экзамена", "")
amo_api.add_custom_field("exam_info", 679707, str, "Информация про экзамен", "")
amo_api.add_custom_field("exam_datetime", 680055, datetime, "Дата экзамена", None, FC.timestamp_to_datetime)

amo_api.add_custom_field("folder_id", 679711, str, "Папка на гугл-диске", "")

amo_api.add_custom_field("is_activated", 679695, bool, "Аккаунт активирован?", False)
amo_api.add_custom_field("has_full_support", 680029, bool, "Куплено сопровождение", False)

amo_api.add_custom_field("access_info", 680071, str, "Информация о доступах", "")
