import json
import logging
import os
from typing import Optional, Tuple, Type
from sqlalchemy.orm.decl_api import DeclarativeMeta

from dotenv import find_dotenv, load_dotenv

from app.connectors.orm import Orm
from app.models.application import Table
from app.models.inference import ApplicationContent, HttpMethod, InferenceResponse
from app.models.message import PostMessageResponse
from app.models.stores.application import Application, ApplicationORM
from app.models.stores.dynamic import create_dynamic_orm

log = logging.getLogger(__name__)

load_dotenv(find_dotenv(filename=".env"))
INTERNAL_DATABASE_URL = os.environ.get("INTERNAL_DATABASE_URL")
EXTERNAL_DATABASE_URL = os.environ.get("EXTERNAL_DATABASE_URL")


# TODO: Abstract the client ORM and internal ORM into the connectors folder (services shouldnt need to load from env in their own files)
class MessageService:
    async def get_application_content_lst(
        self, application_names: list[str]
    ) -> list[ApplicationContent]:
        orm = Orm(url=INTERNAL_DATABASE_URL)
        applications: list[Application] = await orm.get(
            model=ApplicationORM, filters={"name": application_names}
        )
        application_content_lst: list[ApplicationContent] = []
        for application in applications:
            tables: list[Table] = [
                Table.model_validate(table) for table in json.loads(application.tables)
            ]
            application_content = ApplicationContent(
                name=application.name, tables=tables
            )
            application_content_lst.append(application_content)
        return application_content_lst

    async def execute_inference_response(
        self, inference_response: InferenceResponse
    ) -> PostMessageResponse:

        orm = Orm(url=EXTERNAL_DATABASE_URL)

        for http_method_response in inference_response.response:
            target_table: Optional[Table] = None
            for table in http_method_response.application.tables:
                if table.name == http_method_response.table_name:
                    target_table = table
            if not target_table:
                raise ValueError(
                    f"Table {http_method_response.table_name} not found in application {http_method_response.application.name}"
                )

            table_orm_model: Type[DeclarativeMeta] = create_dynamic_orm(
                table=target_table,
                application_name=http_method_response.application.name,
            )
            match http_method_response.http_method:
                case HttpMethod.POST:
                    await orm.insert(
                        model=table_orm_model, data=[http_method_response.inserted_row]
                    )
                case HttpMethod.PUT:
                    await orm.update(
                        model=table_orm_model, data=http_method_response.updated_data
                    )
                case HttpMethod.DELETE:
                    await orm.delete(
                        model=table_orm_model,
                        filters=http_method_response.filter_conditions,
                    )
                case HttpMethod.GET:
                    await orm.get(
                        model=table_orm_model,
                        filters=http_method_response.filter_conditions,
                    )
                case _:
                    raise ValueError(
                        f"Unsupported HTTP method: {http_method_response.http_method}"
                    )
