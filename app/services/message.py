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
from app.models.reverse import ReverseActionDelete, ReverseActionGet, ReverseActionPost, ReverseActionWrapper, ReverseActionUpdate

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
        reverse_stack: list[ReverseActionWrapper],
        inference_response: InferenceResponse
    ) -> PostMessageResponse:        
        response_message_content_lst, response_reverse_action_lst = await _execute(
            inference_response=inference_response
        )
        
        response_message_lst = [Message(
            role=Role.ASSISTANT,
            content=content
        ) for content in response_message_content_lst]
        
        reverse_stack.extend(response_reverse_action_lst)
        chat_history.append(user_message)
        chat_history.extend(response_message_lst)
        
        return PostMessageResponse(
            message_lst=response_message_lst,
            chat_history=chat_history,
            reverse_stack=reverse_stack
        )
        
    async def reverse_inference_response(
        self,
        input: ReverseActionWrapper
    ):
        match input.action.action_type:
            case "delete":
                await _reverse_with_delete(
                    ids=input.action.ids, 
                    table_orm_model=input.action.table_orm_model
                )
            case "get":
                pass
            # case "post":
            #     await _reverse_with_post(
            #         deleted_data=input.action.deleted_data,
            #         table_orm_model=input.action.table_orm_model
            #     )
            # case "update":
            #     await _reverse_with_put(
            #         reverse_updated_data=input.action.reverse_updated_data,
            #         table_orm_model=input.action.table_orm_model
            #     )
            # case _:
            #     raise TypeError("Invalid action type when trying to reverse inferenec response")

###
### REVERSE SECTION
###
async def _reverse_with_delete(
    ids: list[Any],
    table_orm_model: Type[DeclarativeMeta]
):
    orm = Orm(url=EXTERNAL_DATABASE_URL)
    await orm.delete_inference_result(
        model=table_orm_model, 
        filter_conditions=[{"id": id} for id in ids],
        is_and=False
    )
    

###
### INFERENCE SECTION
###
async def _execute(
    inference_response: InferenceResponse
) -> tuple[list[str], list[ReverseActionWrapper]]:
    orm = Orm(url=EXTERNAL_DATABASE_URL)
    response_message_content_lst: list[str] = []
    response_reverse_action_lst: list[ReverseActionWrapper] = []
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
                message_content, reverse_action = await _execute_post_method(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    http_method_response=http_method_response,
                    target_table=target_table,
                    application_name=http_method_response.application.name
                )
            case HttpMethod.PUT:
                message_content, reverse_action = await _execute_put_method(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    http_method_response=http_method_response,
                    target_table=target_table,
                    filter_dict=filter_dict,
                    application_name=http_method_response.application.name
                )
            case HttpMethod.DELETE:
                message_content, reverse_action = await _execute_delete_method(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    http_method_response=http_method_response,
                    target_table=target_table,
                    filter_dict=filter_dict,
                    application_name=http_method_response.application.name
                )
            case HttpMethod.GET:
                message_content, reverse_action = await _execute_get_method(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    http_method_response=http_method_response,
                    target_table=target_table,
                    filter_dict=filter_dict
                )
            case _:
                raise ValueError(
                    f"Unsupported HTTP method: {http_method_response.http_method}"
                )
                
        response_message_content_lst.append(message_content)
        response_reverse_action_lst.append(ReverseActionWrapper(action=reverse_action))

    log.info(response_message_content_lst)
    log.info(response_reverse_action_lst)
    return response_message_content_lst, response_reverse_action_lst

async def _execute_post_method(
    orm: Orm, 
    table_orm_model: Type[DeclarativeMeta], 
    http_method_response: HttpMethodResponse,
    target_table: Table,
    application_name: str
) -> tuple[str, ReverseActionDelete]:
    ids: list[Any] = await orm.post(
        model=table_orm_model, 
        data=http_method_response.inserted_rows
    )
    response_message_content: str = f"The following row(s) has been inserted into the {target_table.name} table of {http_method_response.application.name}:\n{json.dumps(http_method_response.inserted_rows, indent=4)}\n"
    print(type(table_orm_model))
    return response_message_content, ReverseActionDelete(ids=ids, target_table=target_table, application_name=application_name)

async def _execute_put_method(
    orm: Orm, 
    table_orm_model: Type[DeclarativeMeta], 
    http_method_response: HttpMethodResponse,
    target_table: Table,
    filter_dict: dict,
    application_name: str
) -> tuple[str, ReverseActionUpdate]:
    updated_results, reverse_updated_data = await orm.update_inference_result(
        model=table_orm_model, 
        filter_conditions=http_method_response.filter_conditions,
        updated_data=http_method_response.updated_data
    )
    response_message_content: str = f"The following {len(updated_results)} row(s) have been updated in the {target_table.name} table of {http_method_response.application.name} by filtering {json.dumps(filter_dict)}:\n{json.dumps(updated_results, indent=4)}\n"
    return response_message_content, ReverseActionUpdate(reverse_updated_data=reverse_updated_data, target_table=target_table, application_name=application_name)

async def _execute_delete_method(
    orm: Orm, 
    table_orm_model: Type[DeclarativeMeta], 
    http_method_response: HttpMethodResponse,
    target_table: Table,
    filter_dict: dict,
    application_name: str
) -> tuple[str, ReverseActionPost]:
    deleted_data: list[dict[str, Any]] = await orm.delete_inference_result(
        model=table_orm_model,
        filter_conditions=http_method_response.filter_conditions,
    )
    response_message_content: str = f"The following {len(deleted_data)} row(s) have been deleted from the {target_table.name} table of {http_method_response.application.name} by filtering {json.dumps(filter_dict)}:\n{json.dumps(deleted_data, indent=4)}\n"
    for row in deleted_data:
        del row["id"]
    return response_message_content, ReverseActionPost(deleted_data=deleted_data, target_table=target_table, application_name=application_name)

async def _execute_get_method(
    orm: Orm, 
    table_orm_model: Type[DeclarativeMeta], 
    http_method_response: HttpMethodResponse,
    target_table: Table,
    filter_dict: dict
) -> tuple[str, ReverseActionGet]:
    rows: list[dict[str, Any]] = await orm.get_inference_result(
        orm_model=table_orm_model,
        filters=http_method_response.filter_conditions,
    )
    response_message_content: str = f"The following row(s) have been retrieved from the {target_table.name} table of {http_method_response.application.name} by filtering {json.dumps(filter_dict)}:\n{json.dumps(rows, indent=4)}\n"
    return response_message_content, ReverseActionGet()
