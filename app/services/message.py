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
TURSO_INTERNAL_DB_URL = os.environ.get("TURSO_INTERNAL_DB_URL")
TURSO_INTERNAL_DB_AUTH_TOKEN = os.environ.get("TURSO_INTERNAL_DB_AUTH_TOKEN")
TURSO_CLIENT_DB_URL = os.environ.get("TURSO_CLIENT_DB_URL")
TURSO_CLIENT_DB_AUTH_TOKEN = os.environ.get("TURSO_CLIENT_DB_AUTH_TOKEN")

# TODO: Abstract the client ORM and internal ORM into the connectors folder (services shouldnt need to load from env in their own files)
class MessageService:
    async def get_application_content_lst(self, application_ids: list[str]) -> list[ApplicationContent]:
        orm = Orm(url=TURSO_INTERNAL_DB_URL, auth_token=TURSO_INTERNAL_DB_AUTH_TOKEN) 
        applications: list[Application] = orm.get(model=ApplicationORM, filters={"id": application_ids})
        application_content_lst: list[ApplicationContent] = []
        for application in applications:
            tables: list[Table] = [Table.model_validate(table) for table in json.loads(application.tables)]
            application_content = ApplicationContent(
                name=application.name,
                tables=tables
            )
            application_content_lst.append(application_content)
        return application_content_lst
    
    async def execute_inference_response(self, inference_response: InferenceResponse) -> PostMessageResponse:

        orm = Orm(url=TURSO_CLIENT_DB_URL, auth_token=TURSO_CLIENT_DB_AUTH_TOKEN)
        
        for http_method_response in inference_response.response:
            target_table: Optional[Table] = None
            for table in http_method_response.application.tables:
                if table.name == http_method_response.table_name:
                    target_table = table
            if not target_table:
                raise ValueError(f"Table {http_method_response.table_name} not found in application {http_method_response.application.name}")
            
            table_orm_model: Type[DeclarativeMeta] = create_dynamic_orm(
                table=target_table, 
                application_name=http_method_response.application.name
            )
            match http_method_response.http_method:
                case HttpMethod.POST:
                    orm.insert(model=table_orm_model, data=[http_method_response.inserted_row])
                case HttpMethod.PUT:
                    orm.update(model=table_orm_model, data=http_method_response.updated_data)
                case HttpMethod.DELETE:
                    orm.delete(model=table_orm_model, filters=http_method_response.filter_conditions)
                case HttpMethod.GET:
                    orm.get(model=table_orm_model, filters=http_method_response.filter_conditions)
                case _:
                    raise ValueError(f"Unsupported HTTP method: {http_method_response.http_method}")
    