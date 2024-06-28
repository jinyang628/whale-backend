from enum import StrEnum
from pydantic import BaseModel

class ApplicationRequest(BaseModel):
    name: str
    tables: list[dict]

    class Config:
        extra = "forbid"
        
class ApplicationResponse(BaseModel):
    id: str
    
    class Config:
        extra = "forbid"
        
class SelectRequest(BaseModel):
    id: str
    
    class Config:
        extra = "forbid"
     
class SelectResponse(BaseModel):
    name: str
    
    class Config:
        extra = "forbid"   
        
class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: Role
    content: str
    
class MessageRequest(BaseModel):
    message: str
    chat_history: list[Message]
    application_ids: list[str]


class MessageResponse(BaseModel):
    content: str