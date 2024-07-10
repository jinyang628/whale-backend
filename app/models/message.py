from enum import StrEnum
from pydantic import BaseModel

from app.models.reverse import ReverseActionWrapper

class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: Role
    content: str
    
class PostMessageRequest(BaseModel):
    message: str
    chat_history: list[Message]
    reverse_stack: list[ReverseActionWrapper]
    application_names: list[str]


class PostMessageResponse(BaseModel):
    message_lst: list[Message]
    chat_history: list[Message]
    reverse_stack: list[ReverseActionWrapper]