from typing import Optional
from pydantic import BaseModel

from app.models.message.shared import Message
from app.models.message.reverse import ReverseActionWrapper


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
