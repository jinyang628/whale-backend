from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel

from app.models.application.base import ApplicationContent
from app.models.message.use import UseMessage


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class UseInferenceRequest(BaseModel):
    applications: list[ApplicationContent]
    message: str
    chat_history: list[UseMessage]


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
