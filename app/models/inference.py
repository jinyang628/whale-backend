
from pydantic import BaseModel
from app.models.application import ApplicationContent

from app.models.message import Message
    
class InferenceRequest(BaseModel):
    applications: list[ApplicationContent]
    message: str
    chat_history: list[Message]
    
class InferenceResponse(BaseModel):
    content: str