from pydantic import BaseModel

class PostApplicationRequest(BaseModel):
    name: str
    tables: list[dict]

    class Config:
        extra = "forbid"
        
class PostApplicationResponse(BaseModel):
    id: str
    
    class Config:
        extra = "forbid"
        
class SelectApplicationRequest(BaseModel):
    id: str
    
    class Config:
        extra = "forbid"
     
class SelectApplicationResponse(BaseModel):
    name: str
    
    class Config:
        extra = "forbid"   