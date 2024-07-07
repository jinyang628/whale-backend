import json
import logging
import os
from typing import Any, Optional, Type
from sqlalchemy.orm.decl_api import DeclarativeMeta

from dotenv import find_dotenv, load_dotenv

from app.connectors.orm import Orm
from app.models.application import PrimaryKey, Table
from app.models.inference import ApplicationContent, HttpMethod, InferenceResponse
from app.models.message import Message, PostMessageResponse, Role
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
        applications: list[Application] = await orm.get_application(
            orm_model=ApplicationORM, 
            pydantic_model=Application,
            names=application_names
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
        self, 
        user_message: Message,
        chat_history: list[Message],
        inference_response: InferenceResponse
    ) -> PostMessageResponse:

        orm = Orm(url=EXTERNAL_DATABASE_URL)
        chat_history.append(user_message)
        response_message_content: str = ""
        for http_method_response in inference_response.response:
            target_table: Optional[Table] = None
            for table in http_method_response.application.tables:
                if table.name == http_method_response.table_name:
                    target_table = table
            if not target_table:
                raise ValueError(
                    f"Table {http_method_response.table_name} not found in application {http_method_response.application.name}"
                )
                
            primary_key: Optional[PrimaryKey] = None
            for column in target_table.columns:
                if column.primary_key == PrimaryKey.NONE:
                    continue
                primary_key = column.primary_key
                break
            if not primary_key:
                raise TypeError(
                    f"Table {target_table.name} does not have a primary key"
                )
                
            table_orm_model: Type[DeclarativeMeta] = create_dynamic_orm(
                table=target_table,
                application_name=http_method_response.application.name,
            )
                            
            match http_method_response.http_method:
                case HttpMethod.POST:
                    await orm.insert(
                        model=table_orm_model, data=http_method_response.inserted_rows
                    )
                    response_message_content += f"The following row(s) has been inserted:\n{json.dumps(http_method_response.inserted_rows, indent=4)}\n"
                case HttpMethod.PUT:
                    updated_data: list[dict[str, Any]] = await orm.update_inference_result(
                        model=table_orm_model, 
                        filter_conditions=http_method_response.filter_conditions,
                        updated_data=http_method_response.updated_data
                    )
                    response_message_content += f"The following {len(updated_data)} row(s) have been updated:\n{json.dumps(updated_data, indent=4)}\n"
                case HttpMethod.DELETE:
                    deleted_data: list[dict[str, Any]] = await orm.delete_inference_result(
                        model=table_orm_model,
                        filter_conditions=http_method_response.filter_conditions,
                    )
                    response_message_content += f"The following {len(deleted_data)} row(s) have been deleted:\n{json.dumps(deleted_data, indent=4)}\n"
                case HttpMethod.GET:
                    rows: list[dict[str, Any]] = await orm.get_inference_result(
                        orm_model=table_orm_model,
                        filters=http_method_response.filter_conditions,
                    )
                    response_message_content += f"The following row(s) have been retrieved: {json.dumps(rows, indent=4)}\n"
                case _:
                    raise ValueError(
                        f"Unsupported HTTP method: {http_method_response.http_method}"
                    )
            
        response_message = Message(
            role=Role.ASSISTANT,
            content=response_message_content
        ) 
        chat_history.append(response_message)
        return PostMessageResponse(
            message=response_message,
            chat_history=chat_history
        )
