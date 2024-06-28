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
        