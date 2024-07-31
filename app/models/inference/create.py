from typing import Optional

from pydantic import BaseModel

from app.models.application.base import ApplicationContent
from app.models.message.create import CreateMessage


class CreateInferenceRequest(BaseModel):
    message: str
    chat_history: list[CreateMessage]


class CreateInferenceResponse(BaseModel):
    application_content: Optional[ApplicationContent] = None
    overview: Optional[str] = None
    clarification: Optional[str] = None
    concluding_message: Optional[str] = None
