import logging
import os
from typing import Optional

from dotenv import find_dotenv, load_dotenv

from app.connectors.orm import Orm
from app.models.stores.application import Application, ApplicationORM
from app.models.application import PostApplicationRequest, PostApplicationResponse, SelectApplicationRequest, SelectApplicationResponse

log = logging.getLogger(__name__)

load_dotenv(find_dotenv(filename=".env"))
TURSO_INTERNAL_DB_URL = os.environ.get("TURSO_INTERNAL_DB_URL")
TURSO_INTERNAL_DB_AUTH_TOKEN = os.environ.get("TURSO_INTERNAL_DB_AUTH_TOKEN")

class ApplicationService:
    
    async def post(self, input: PostApplicationRequest) -> PostApplicationResponse:
        """Inserts the entry into the application table."""
        application = Application.local(
            name=input.name,
            tables=input.tables
        )
        orm = Orm(url=TURSO_INTERNAL_DB_URL, auth_token=TURSO_INTERNAL_DB_AUTH_TOKEN)
        orm.insert(models=[application])
        return PostApplicationResponse(id=application.id)
    
    async def select(self, input: SelectApplicationRequest) -> Optional[SelectApplicationResponse]:
        """Selects the entry from the application table."""
        orm = Orm(url=TURSO_INTERNAL_DB_URL, auth_token=TURSO_INTERNAL_DB_AUTH_TOKEN)
        result: list[Application] = orm.get(model=ApplicationORM, filters={"id": input.id})
        if len(result) != 1:
            return None
        return SelectApplicationResponse(
            name=result[0].name
        )