import logging
import os

from dotenv import find_dotenv, load_dotenv

from app.connectors.orm import Orm
from app.models.stores.application import Application, ApplicationORM

log = logging.getLogger(__name__)

load_dotenv(find_dotenv(filename=".env"))
TURSO_DB_URL = os.environ.get("TURSO_DB_URL")
TURSO_DB_AUTH_TOKEN = os.environ.get("TURSO_DB_AUTH_TOKEN")

class MessageService:
    async def get_applications(self, application_ids: list[str]) -> list[Application]:
        orm = Orm(url=TURSO_DB_URL, auth_token=TURSO_DB_AUTH_TOKEN) 
        result: list[Application] = orm.get(model=ApplicationORM, filters={"id": application_ids})
        return result