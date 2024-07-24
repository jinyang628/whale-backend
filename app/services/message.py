import copy
import json
import logging
from typing import Any, Optional, Type
from sqlalchemy.orm.decl_api import DeclarativeMeta
import uuid
from app.connectors.orm import Orm
from app.models.application import Table
from app.models.inference import ApplicationContent, HttpMethod, HttpMethodResponse, InferenceResponse
from app.models.message import Message, PostMessageResponse, Role
from app.models.stores.application import Application, ApplicationORM
from app.models.stores.dynamic import create_dynamic_orm
from app.models.reverse import ReverseActionClarification, ReverseActionDelete, ReverseActionGet, ReverseActionPost, ReverseActionWrapper, ReverseActionUpdate
from app.stores.utils.frontend_message import translate_filter_dict
from app.stores.utils.process import identify_columns_to_process, process_client_facing_filter_dict, process_client_facing_update_dict, process_datetime_or_date_values_of_filter_dict, process_datetime_or_date_values_of_update_dict, process_datetime_values_of_row, process_client_facing_rows

log = logging.getLogger(__name__)


# TODO: Abstract the client ORM and internal ORM into the connectors folder (services shouldnt need to load from env in their own files)
class MessageService:
    
    async def get_application_content_lst(
        self, application_names: list[str]
    ) -> list[ApplicationContent]:
        orm = Orm(is_user_facing=False)
        applications: list[Application] = await orm.static_get(
            orm_model=ApplicationORM, 
            pydantic_model=Application,
            filters={"boolean_clause": "OR", "conditions": [{"column": "name", "operator": "=", "value": name} for name in application_names]}
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
        if inference_response.clarification:
            response_message_lst = [Message(role=Role.ASSISTANT, content=inference_response.clarification)]
            chat_history.append(user_message)
            chat_history.extend(response_message_lst)
            reverse_stack.append(ReverseActionWrapper(action=ReverseActionClarification()))
            return PostMessageResponse(
                message_lst=response_message_lst,
                chat_history=chat_history,
                reverse_stack=reverse_stack
            )    
             
        response_message_lst, response_reverse_action_lst = await _execute(
            inference_response=inference_response
        )
        
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
        if input.action.action_type == "get" or input.action.action_type == "clarification":
            return
        
        orm = Orm(is_user_facing=True)
        table_orm_model: Type[DeclarativeMeta] = create_dynamic_orm(
            table=input.action.target_table,
            application_name=input.action.application_name
        )
        match input.action.action_type:
            case "delete":
                await _reverse_with_delete(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    ids=input.action.ids
                )
            case "post":
                await _reverse_with_post(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    deleted_data=input.action.deleted_data
                )
            case "update":
                await _reverse_with_put(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    reverse_filter_conditions=input.action.reverse_filter_conditions,
                    reverse_updated_data=input.action.reverse_updated_data
                )
            case _:
                raise TypeError("Invalid action type when trying to reverse inferenec response")

###
### REVERSE SECTION
###
async def _reverse_with_delete(
    orm: Orm,
    table_orm_model: Type[DeclarativeMeta],
    ids: list[Any],
):
    print(ids)
    ids_lst: list[Any] = []
    for id in ids:
        # Convert the string uuid back to UUID object (It had to be a string because UUID is not JSON serialisable as an API request object)
        if isinstance(id, str):
            ids_lst.append(uuid.UUID(id))
        # AUTO_INCREMENT primary key
        elif isinstance(id, int): 
            ids_lst.append(id)
        else:
            raise TypeError("Invalid type for id in reverse action")

    await orm.delete_inference_result(
        model=table_orm_model, 
        filters={"id": ids_lst[0]}, ## TODO: Fix this problematic temp fix to allow reverse of multiple entries
        is_and=False
    )
    
async def _reverse_with_post(
    orm: Orm,
    table_orm_model: Type[DeclarativeMeta],
    deleted_data: list[dict[str, Any]]
):
    for row in deleted_data:
        del[row["created_at"]]
        del[row["updated_at"]]
        
    await orm.post(
        model=table_orm_model, 
        data=deleted_data
    )
    
async def _reverse_with_put(
    orm: Orm,
    table_orm_model: Type[DeclarativeMeta],
    reverse_filter_conditions: dict[str, Any],
    reverse_updated_data: dict[str, Any]
):
    await orm.update_inference_result(
        model=table_orm_model,
        filters=reverse_filter_conditions,
        updated_data=reverse_updated_data
    )
    
###
### INFERENCE SECTION
###
async def _execute(
    inference_response: InferenceResponse
) -> tuple[list[Message], list[ReverseActionWrapper]]:
    orm = Orm(is_user_facing=True)
    response_message_content_lst: list[Message] = []
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
            application_name=http_method_response.application.name
        )
            
        match http_method_response.http_method:
            case HttpMethod.POST:
                log.info("Executing POST request")
                content, rows, reverse_action = await _execute_post_method(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    http_method_response=http_method_response,
                    target_table=target_table,
                    application_name=http_method_response.application.name
                )
            case HttpMethod.PUT:
                log.info("Executing PUT request")
                content, rows, reverse_action = await _execute_put_method(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    target_table=target_table,
                    filter_dict=http_method_response.filter_conditions,
                    update_dict=http_method_response.updated_data,
                    application_name=http_method_response.application.name
                )
            case HttpMethod.DELETE:
                log.info("Executing DELETE request")
                content, rows, reverse_action = await _execute_delete_method(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    http_method_response=http_method_response,
                    target_table=target_table,
                    filter_dict=http_method_response.filter_conditions,
                    application_name=http_method_response.application.name
                )
            case HttpMethod.GET:
                log.info("Executing GET request")
                content, rows, reverse_action = await _execute_get_method(
                    orm=orm,
                    table_orm_model=table_orm_model,
                    application_name=http_method_response.application.name,
                    target_table=target_table,
                    filter_dict=http_method_response.filter_conditions
                )
            case _:
                raise ValueError(
                    f"Unsupported HTTP method: {http_method_response.http_method}"
                )
                
        message = Message(
            role=Role.ASSISTANT,
            content=content,
            rows=rows
        )
                
        response_message_content_lst.append(message)
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
) -> tuple[str, list[dict[str, Any]], ReverseActionDelete]:
    
    copied_rows: list[dict[str, Any]] = copy.deepcopy(http_method_response.inserted_rows)
    
    log.info("Processing data for POST request")
    datetime_column_names_to_process, date_column_names_to_process = identify_columns_to_process(
        table=target_table
    )
    rows_to_insert: list[dict[str, Any]] = process_datetime_values_of_row(
        rows=copied_rows, 
        datetime_column_names_to_process=datetime_column_names_to_process,
        date_column_names_to_process=date_column_names_to_process
    )

    log.info("Initiating POST request")
    ids, rows = await orm.post(
        model=table_orm_model, 
        data=rows_to_insert
    )
    log.info(f"Rows from POST request: {rows}")


    message_content: str = f"The following row(s) has been inserted into the {target_table.name} table of {http_method_response.application.name}:"
    
    return message_content, rows, ReverseActionDelete(ids=ids, target_table=target_table, application_name=application_name)

async def _execute_put_method(
    orm: Orm, 
    table_orm_model: Type[DeclarativeMeta], 
    target_table: Table,
    filter_dict: dict,
    update_dict: dict,
    application_name: str
) -> tuple[str, list[dict[str, Any]], ReverseActionUpdate]:
    copied_filter_dict: list[dict[str, Any]] = copy.deepcopy(filter_dict)
    copied_update_dict: list[dict[str, Any]] = copy.deepcopy(update_dict)
    
    log.info("Processing data for PUT request")
    datetime_column_names_to_process, date_column_names_to_process = identify_columns_to_process(
        table=target_table
    )
    copied_filter_dict = process_datetime_or_date_values_of_filter_dict(
        dict_to_process=copied_filter_dict,
        datetime_column_names_to_process=datetime_column_names_to_process,
        date_column_names_to_process=date_column_names_to_process
    )
    
    copied_update_dict = process_datetime_or_date_values_of_update_dict(
        dict_to_process=copied_update_dict,
        datetime_column_names_to_process=datetime_column_names_to_process,
        date_column_names_to_process=date_column_names_to_process
    )
    
    log.info("Initiating PUT request")
    rows, reverse_filters, reverse_updated_data = await orm.update_inference_result(
        model=table_orm_model, 
        filters=copied_filter_dict,
        updated_data=copied_update_dict
    )
    log.info(f"Rows from PUT request: {rows}")
    
    rows = process_client_facing_rows(
        db_rows=rows,
        datetime_column_names_to_process=datetime_column_names_to_process,
        date_column_names_to_process=date_column_names_to_process
    )
    
    reverse_filters = process_client_facing_filter_dict(
        db_dict=reverse_filters,
        datetime_column_names_to_process=datetime_column_names_to_process,
        date_column_names_to_process=date_column_names_to_process
    )
    
    reverse_updated_data = process_client_facing_update_dict(
        db_dict=reverse_updated_data,
        datetime_column_names_to_process=datetime_column_names_to_process,
        date_column_names_to_process=date_column_names_to_process
    )
    
    message_content: str = ""
    if not filter_dict["conditions"]:
        message_content = f"All the {len(rows)} row(s) have been updated in the {target_table.name} table of {application_name}:"
    else:
        message_content = f"The following {len(rows)} row(s) have been updated in the {target_table.name} table of {application_name} by filtering {translate_filter_dict(filter_dict)}:"
    
    return message_content, rows, ReverseActionUpdate(
        reverse_filter_conditions=reverse_filters, 
        reverse_updated_data=reverse_updated_data, 
        target_table=target_table, 
        application_name=application_name
        )

async def _execute_delete_method(
    orm: Orm, 
    table_orm_model: Type[DeclarativeMeta], 
    http_method_response: HttpMethodResponse,
    target_table: Table,
    filter_dict: dict[str, Any],
    application_name: str
) -> tuple[str, list[dict[str, Any]], ReverseActionPost]:
    
    copied_filter_dict: list[dict[str, Any]] = copy.deepcopy(filter_dict)

    log.info("Processing data for DELETE request")
    datetime_column_names_to_process, date_column_names_to_process = identify_columns_to_process(
        table=target_table
    )
    copied_filter_dict = process_datetime_or_date_values_of_filter_dict(
        dict_to_process=copied_filter_dict,
        datetime_column_names_to_process=datetime_column_names_to_process,
        date_column_names_to_process=date_column_names_to_process
    )
    
    log.info("Initiating DELETE request")
    rows: list[dict[str, Any]] = await orm.delete_inference_result(
        model=table_orm_model,
        filters=filter_dict,
    )
    log.info(f"Rows from DELETE request: {rows}")
    
    rows = process_client_facing_rows(
        db_rows=rows,
        datetime_column_names_to_process=datetime_column_names_to_process,
        date_column_names_to_process=date_column_names_to_process
    )
    
    message_content: str = ""
    if not filter_dict["conditions"]:
        message_content = f"All the {len(rows)} row(s) have been deleted from the {target_table.name} table of {http_method_response.application.name}:"
    else:
        message_content: str = f"The following {len(rows)} row(s) have been deleted from the {target_table.name} table of {http_method_response.application.name} by filtering {translate_filter_dict(filter_dict)}:"
    
    return message_content, rows, ReverseActionPost(
        deleted_data=rows, 
        target_table=target_table, 
        application_name=application_name
    )

async def _execute_get_method(
    orm: Orm, 
    table_orm_model: Type[DeclarativeMeta], 
    application_name: str,
    target_table: Table,
    filter_dict: dict[str, Any]
) -> tuple[str, list[dict[str,Any]], ReverseActionGet]:
    
    copied_filter_dict: list[dict[str, Any]] = copy.deepcopy(filter_dict)

    log.info("Processing data for GET request")
    datetime_column_names_to_process, date_column_names_to_process = identify_columns_to_process(
        table=target_table
    )
    copied_filter_dict = process_datetime_or_date_values_of_filter_dict(
        dict_to_process=copied_filter_dict,
        datetime_column_names_to_process=datetime_column_names_to_process,
        date_column_names_to_process=date_column_names_to_process
    )
    
    log.info("Initiating GET request")
    rows: list[dict[str, Any]] = await orm.get_inference_result(
        model=table_orm_model,
        filters=copied_filter_dict,
    )
    log.info(f"Rows from GET request: {rows}")

    rows = process_client_facing_rows(
        db_rows=rows,
        datetime_column_names_to_process=datetime_column_names_to_process,
        date_column_names_to_process=date_column_names_to_process
    )
    
    
    message_content: str = ""
    if not filter_dict["conditions"]:
        message_content = f"All the {len(rows)} row(s) have been retrieved from the {target_table.name} table of {application_name}:"
    else:
        message_content = f"The following row(s) have been retrieved from the {target_table.name} table of {application_name} by filtering {translate_filter_dict(filter_dict)}:"

    return message_content, rows, ReverseActionGet()
