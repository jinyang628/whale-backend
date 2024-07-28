from typing import Any, Optional
from pydantic import BaseModel
from enum import StrEnum
from app.models.application import ApplicationContent

from app.models.message.shared import Message


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class UseInferenceRequest(BaseModel):
    applications: list[ApplicationContent]
    message: str
    chat_history: list[Message]


class HttpMethodResponse(BaseModel):
    http_method: HttpMethod
    application: ApplicationContent
    table_name: str
    inserted_rows: Optional[list[dict[str, Any]]] = None
    filter_conditions: Optional[dict[str, Any]] = None
    updated_data: Optional[dict[str, Any]] = None


class UseInferenceResponse(BaseModel):
    response: list[HttpMethodResponse]
    clarification: Optional[str] = None
