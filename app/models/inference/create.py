from typing import Optional
from pydantic import BaseModel
from app.models.application import ApplicationContent

from app.models.message.shared import Message

class CreateInferenceRequest(BaseModel):
    message: str
    chat_history: list[Message]

class CreateInferenceResponse(BaseModel):
    nessage: str
    application: Optional[ApplicationContent]
