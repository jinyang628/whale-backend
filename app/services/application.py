import json
import logging
from typing import Optional

from app.connectors.orm import Orm
from app.models.stores.application import Application, ApplicationORM
from app.models.application import (
    ApplicationContent,
    PostApplicationRequest,
    PostApplicationResponse,
    SelectApplicationResponse,
    Table,
)
from app.stores.base.main import execute_client_script
from app.stores.sqls.template import generate_foreign_key_script, generate_table_creation_script

log = logging.getLogger(__name__)


class ApplicationService:

    async def post(self, input: PostApplicationRequest) -> PostApplicationResponse:
        """Inserts the entry into the application table."""
        tables_dump: list[dict] = [table.model_dump() for table in input.tables]
        application = Application.local(name=input.name, tables=tables_dump)
        orm = Orm(is_user_facing=False)
        await orm.post(model=ApplicationORM, data=[application.model_dump()])
        return PostApplicationResponse(name=application.name)

    async def generate_client_application(
        self, input: PostApplicationRequest
    ) -> PostApplicationResponse:
        """Generates the client application."""
        # Step 1: Create tables
        for table in input.tables:
            # Prefix application name so that the table name remains unique amidst other client applications. Client application name is enforced to be unique
            table_name = f"{input.name}_{table.name}"
            
            # For input of inference, we will GET table description from the internal database, and the table name and columns from the client database
            # For output of inference, we will simply modify the entries in the client database associated with the user's API key
            table_script: str = generate_table_creation_script(
                table_name=table_name, 
                columns=table.columns
            )
            await execute_client_script(
                table_name=table_name,
                sql_script=table_script,
            )

        # Step 2: Add foreign key constraints
        for table in input.tables:
            table_name = f"{input.name}_{table.name}"
            foreign_key_script = generate_foreign_key_script(
                input_name=input.name, 
                table_name=table_name, 
                columns=table.columns
            )
            if not foreign_key_script:
                continue
            await execute_client_script(
                table_name=table_name,
                sql_script=foreign_key_script,
            )

    async def select(
        self, name: str
    ) -> Optional[SelectApplicationResponse]:
        """Selects the entry from the application table."""
        orm = Orm(is_user_facing=False)
        result: list[Application] = await orm.get_application(
            orm_model=ApplicationORM, pydantic_model=Application, names=[name]
        )
        if len(result) != 1:
            return None
        app: Application = result[0]
        application_content = ApplicationContent(
            name=app.name,
            tables=[Table.model_validate(table) for table in json.loads(app.tables)],
        )
        return SelectApplicationResponse(application=application_content)
