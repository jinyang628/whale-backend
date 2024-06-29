
from pydantic import BaseModel

from app.models.message import Message
    
class ApplicationContent(BaseModel):
    name: str
    tables: str
    
class InferenceRequest(BaseModel):
    applications: list[ApplicationContent]
    message: str
    chat_history: list[Message]
    
class InferenceResponse(BaseModel):
    content: str