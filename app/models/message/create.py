from typing import Optional
from pydantic import BaseModel
from app.models.application.base import ApplicationContent

from app.models.message.shared import Message

class CreateMessage(Message):
    application_content: Optional[ApplicationContent] = None
    
class CreateRequest(BaseModel):
    message: str
    chat_history: list[CreateMessage]

class CreateResponse(BaseModel):
    message: CreateMessage
    chat_history: list[CreateMessage]
    is_finished: bool
    