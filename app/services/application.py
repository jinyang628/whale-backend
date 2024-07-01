import logging
import os
from typing import Optional

from dotenv import find_dotenv, load_dotenv

from app.connectors.orm import Orm
from app.models.stores.application import Application, ApplicationORM
from app.models.application import PostApplicationRequest, PostApplicationResponse, SelectApplicationRequest, SelectApplicationResponse
from app.stores.base.main import generate_client_table

log = logging.getLogger(__name__)

load_dotenv(find_dotenv(filename=".env"))
INTERNAL_DATABASE_URL = os.environ.get("INTERNAL_DATABASE_URL")
EXTERNAL_DATABASE_URL = os.environ.get("EXTERNAL_DATABASE_URL")

class ApplicationService:
    
    async def post(self, input: PostApplicationRequest) -> PostApplicationResponse:
        """Inserts the entry into the application table."""
        tables_dump: list[dict] = [table.model_dump() for table in input.tables]
        application = Application.local(
            name=input.name,
            tables=tables_dump
        )
        orm = Orm(url=INTERNAL_DATABASE_URL)
        await orm.insert(model=ApplicationORM, data=[application.model_dump()])
        return PostApplicationResponse.from_uuid(application.id)
    
    async def generate_client_application(self, input: PostApplicationRequest) -> PostApplicationResponse:
        """Generates the client application."""
        for table in input.tables:
            # Prefix application name so that the table name remains unique amidst other client applications. Client application name is enforced to be unique
            table_name = f"{input.name}_{table.name}" 
            # For input of inference, we will GET table description from the internal database, and the table name and columns from the client database
            # For output of inference, we will simply modify the entries in the client database associated with the user's API key
            await generate_client_table(
                table_name=table_name, 
                columns=table.columns, 
                db_url=EXTERNAL_DATABASE_URL, 
            )
    
    async def select(self, input: SelectApplicationRequest) -> Optional[SelectApplicationResponse]:
        """Selects the entry from the application table."""
        orm = Orm(url=INTERNAL_DATABASE_URL)
        result: list[Application] = await orm.get(model=ApplicationORM, filters={"id": input.id})
        if len(result) != 1:
            return None
        print(result)
        return SelectApplicationResponse(
            name=result[0].name
        )