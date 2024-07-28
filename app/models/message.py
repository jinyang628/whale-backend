from enum import StrEnum
from typing import Any, Optional
from pydantic import BaseModel

from app.models.reverse import ReverseActionWrapper


class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: Role
    content: str
    blocks: Optional[list[dict[str, Any]]] = None


class UseRequest(BaseModel):
    message: str
    chat_history: list[Message]
    reverse_stack: list[ReverseActionWrapper]
    application_names: list[str]
    user_id: str


class UseResponse(BaseModel):
    message_lst: list[Message]
    chat_history: list[Message]
    reverse_stack: list[ReverseActionWrapper]
    clarification: Optional[str] = None
