from pydantic import BaseModel

from app.models.message.shared import Message


class CreateRequest(BaseModel):
    message: str
    chat_history: list[Message]

class CreateResponse(BaseModel):
    message: Message
    chat_history: list[Message]