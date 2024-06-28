import logging
import os
from typing import Optional

from dotenv import find_dotenv, load_dotenv


from app.models.types import MessageRequest, MessageResponse

log = logging.getLogger(__name__)

load_dotenv(find_dotenv(filename=".env"))
TURSO_DB_URL = os.environ.get("TURSO_DB_URL")
TURSO_DB_AUTH_TOKEN = os.environ.get("TURSO_DB_AUTH_TOKEN")

class MessageService:
    pass