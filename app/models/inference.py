
from typing import Any, Optional
from pydantic import BaseModel
from enum import StrEnum
from app.models.application import ApplicationContent

from app.models.message import Message

class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    
class InferenceRequest(BaseModel):
    applications: list[ApplicationContent]
    message: str
    chat_history: list[Message]
    
class HttpMethodResponse(BaseModel):
    http_method: HttpMethod
    application: ApplicationContent
    table_name: str
    inserted_rows: Optional[list[dict[str, Any]]] = None
    filter_conditions: Optional[list[dict[str, Any]]] = None
    updated_data: Optional[list[dict[str, Any]]] = None
    
class InferenceResponse(BaseModel):
    response: list[HttpMethodResponse]
    