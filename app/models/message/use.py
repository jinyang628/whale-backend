from typing import Any, Optional

from pydantic import BaseModel

from app.models.message.reverse import ReverseActionWrapper
from app.models.message.shared import Message


class UseMessage(Message):
    rows: Optional[list[dict[str, Any]]] = None


class UseRequest(BaseModel):
    message: str
    chat_history: list[UseMessage]
    reverse_stack: list[ReverseActionWrapper]
    application_names: list[str]
    user_id: str


class UseResponse(BaseModel):
    message_lst: list[UseMessage]
    chat_history: list[UseMessage]
    reverse_stack: list[ReverseActionWrapper]
    clarification: Optional[str] = None
