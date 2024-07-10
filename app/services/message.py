import json
import logging
import os
from typing import Any, Optional, Type
from sqlalchemy.orm.decl_api import DeclarativeMeta

from dotenv import find_dotenv, load_dotenv

from app.connectors.orm import Orm
from app.models.application import Table
from app.models.inference import ApplicationContent, HttpMethod, HttpMethodResponse, InferenceResponse
from app.models.message import Message, PostMessageResponse, Role
from app.models.stores.application import Application, ApplicationORM
from app.models.stores.dynamic import create_dynamic_orm
from app.models.reverse import Delete, Get, Post, ReverseActionWrapper, Update

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
        response_message_content, reverse_stack = await _execute(
            inference_response=inference_response
        )
            
        response_message = Message(
            role=Role.ASSISTANT,
            content=response_message_content
        ) 
        chat_history.extend([user_message, response_message])
        return PostMessageResponse(
            message=response_message,
            chat_history=chat_history,
            reverse_stack=reverse_stack
        )
        
async def _execute(
    inference_response: InferenceResponse
) -> tuple[str, list[ReverseActionWrapper]]:
    orm = Orm(url=EXTERNAL_DATABASE_URL)
    response_message_content: str = ""
    reverse_stack: list[ReverseActionWrapper] = []
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
        filter_dict: Optional[dict] = None
        if http_method_response.filter_conditions:
            filter_dict = {cond['column_name']: cond['column_value'] for cond in http_method_response.filter_conditions}
            
        match http_method_response.http_method:
            case HttpMethod.POST:
                message_content, delete_action = await _execute_post_method(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    http_method_response=http_method_response,
                    target_table=target_table
                )
                response_message_content += message_content
                reverse_stack.append(ReverseActionWrapper(action=delete_action))
            case HttpMethod.PUT:
                message_content, update_action = await _execute_put_method(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    http_method_response=http_method_response,
                    target_table=target_table,
                    filter_dict=filter_dict
                )
                response_message_content += message_content
                reverse_stack.append(ReverseActionWrapper(action=update_action))
            case HttpMethod.DELETE:
                message_content, post_action = await _execute_delete_method(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    http_method_response=http_method_response,
                    target_table=target_table,
                    filter_dict=filter_dict
                )
                response_message_content += message_content
                reverse_stack.append(ReverseActionWrapper(action=post_action))
            case HttpMethod.GET:
                message_content, get_action = await _execute_get_method(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    http_method_response=http_method_response,
                    target_table=target_table,
                    filter_dict=filter_dict
                )
                response_message_content += message_content
                reverse_stack.append(ReverseActionWrapper(action=get_action))
            case _:
                raise ValueError(
                    f"Unsupported HTTP method: {http_method_response.http_method}"
                )
    log.info(response_message_content)
    log.info(reverse_stack)
    return response_message_content, reverse_stack

async def _execute_post_method(
    orm: Orm, 
    table_orm_model: Type[DeclarativeMeta], 
    http_method_response: HttpMethodResponse,
    target_table: Table
) -> tuple[str, Delete]:
    ids: list[Any] = await orm.post(
        model=table_orm_model, 
        data=http_method_response.inserted_rows
    )
    response_message_content: str = f"The following row(s) has been inserted into the {target_table.name} table of {http_method_response.application.name}:\n{json.dumps(http_method_response.inserted_rows, indent=4)}\n"
    return response_message_content, Delete(ids=ids)

async def _execute_put_method(
    orm: Orm, 
    table_orm_model: Type[DeclarativeMeta], 
    http_method_response: HttpMethodResponse,
    target_table: Table,
    filter_dict: dict
) -> tuple[str, Update]:
    updated_results, reverse_updated_data = await orm.update_inference_result(
        model=table_orm_model, 
        filter_conditions=http_method_response.filter_conditions,
        updated_data=http_method_response.updated_data
    )
    response_message_content: str = f"The following {len(updated_results)} row(s) have been updated in the {target_table.name} table of {http_method_response.application.name} by filtering {json.dumps(filter_dict)}:\n{json.dumps(updated_results, indent=4)}\n"
    return response_message_content, Update(reverse_updated_data=reverse_updated_data)

async def _execute_delete_method(
    orm: Orm, 
    table_orm_model: Type[DeclarativeMeta], 
    http_method_response: HttpMethodResponse,
    target_table: Table,
    filter_dict: dict
) -> tuple[str, Post]:
    deleted_data: list[dict[str, Any]] = await orm.delete_inference_result(
        model=table_orm_model,
        filter_conditions=http_method_response.filter_conditions,
    )
    response_message_content: str = f"The following {len(deleted_data)} row(s) have been deleted from the {target_table.name} table of {http_method_response.application.name} by filtering {json.dumps(filter_dict)}:\n{json.dumps(deleted_data, indent=4)}\n"
    for row in deleted_data:
        del row["id"]
    return response_message_content, Post(deleted_data=deleted_data)

async def _execute_get_method(
    orm: Orm, 
    table_orm_model: Type[DeclarativeMeta], 
    http_method_response: HttpMethodResponse,
    target_table: Table,
    filter_dict: dict
) -> tuple[str, Get]:
    rows: list[dict[str, Any]] = await orm.get_inference_result(
        orm_model=table_orm_model,
        filters=http_method_response.filter_conditions,
    )
    response_message_content: str = f"The following row(s) have been retrieved from the {target_table.name} table of {http_method_response.application.name} by filtering {json.dumps(filter_dict)}:\n{json.dumps(rows, indent=4)}\n"
    return response_message_content, Get()