from enum import StrEnum
from pydantic import BaseModel

class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: Role
    content: str
    
class PostMessageRequest(BaseModel):
    message: str
    chat_history: list[Message]
    application_names: list[str]


class PostMessageResponse(BaseModel):
    content: str
    chat_history: list[Message]