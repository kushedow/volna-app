import os

from loguru import logger


GDRIVE_URL = "https://script.google.com/macros/s/AKfycbwJpmxd3x3mysp53z5AYxf0xwqUYRz1VwJRAWnQyPRfjCz0dG7iJvs6p-Vk2Z1iX1GN/exec?query="

CUSTOMERS_URL = GDRIVE_URL + "/customers"
SPECIALITIES_URL = GDRIVE_URL + "/specialities"
DOCUMENTS_URL = GDRIVE_URL + "/documents"
UPLOAD_URL = GDRIVE_URL + "/upload"
FAQ_URL = GDRIVE_URL + "/faq"
GROUPS_URL = GDRIVE_URL + "/groups"
EVENTS_URL = GDRIVE_URL + "/events"
CONFIG_URL = GDRIVE_URL + "/config"

AMO_BASE_URL = "https://xeniaceo.kommo.com"
AMO_ACCESS_TOKEN = os.getenv("AMO_ACCESS_TOKEN")

ALLOWED_EXTENSIONS = ["pdf"]
UPLOAD_FOLDER = "uploads"

logger.add( UPLOAD_FOLDER + "/file_{time}.log", rotation="12:00")


