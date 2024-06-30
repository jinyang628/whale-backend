import json
import logging
import os

from dotenv import find_dotenv, load_dotenv

from app.connectors.orm import Orm
from app.models.inference import ApplicationContent, HttpMethod, InferenceResponse
from app.models.message import PostMessageResponse
from app.models.stores.application import Application, ApplicationORM

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
        application_content_lst: list[ApplicationContent] = [
            ApplicationContent(
                name=application.name,
                tables=json.loads(application.tables)
            )    
            for application in applications
        ]
        return application_content_lst
    
    async def execute_inference_response(self, inference_response: InferenceResponse) -> PostMessageResponse:
        orm = Orm(url=TURSO_CLIENT_DB_URL, auth_token=TURSO_CLIENT_DB_AUTH_TOKEN)
        for http_method_response in inference_response.response:
            match http_method_response.http_method:
                case HttpMethod.POST:
                    orm.insert(model=ApplicationORM, data=inference_response.inserted_row)
                case HttpMethod.PUT:
                    orm.put(model=ApplicationORM, data=inference_response.updated_data)
                case HttpMethod.DELETE:
                    orm.delete(model=ApplicationORM, filters=inference_response.filter_conditions)
                case HttpMethod.GET:
                    orm.get(model=ApplicationORM, filters=inference_response.filter_conditions)
                case _:
                    raise ValueError(f"Unsupported HTTP method: {http_method_response.http_method}")
    