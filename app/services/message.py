import logging
import os

from dotenv import find_dotenv, load_dotenv

from app.connectors.orm import Orm
from app.models.inference import ApplicationContent
from app.models.stores.application import Application, ApplicationORM

log = logging.getLogger(__name__)

load_dotenv(find_dotenv(filename=".env"))
TURSO_DB_URL = os.environ.get("TURSO_DB_URL")
TURSO_DB_AUTH_TOKEN = os.environ.get("TURSO_DB_AUTH_TOKEN")

class MessageService:
    async def get_application_content_lst(self, application_ids: list[str]) -> list[ApplicationContent]:
        orm = Orm(url=TURSO_DB_URL, auth_token=TURSO_DB_AUTH_TOKEN) 
        applications: list[Application] = orm.get(model=ApplicationORM, filters={"id": application_ids})
        application_content_lst: list[ApplicationContent] = [
            ApplicationContent(
                name=application.name,
                tables=application.tables
            )    
            for application in applications
        ]
        return application_content_lst