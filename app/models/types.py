from pydantic import BaseModel

class EntryRequest(BaseModel):
    name: str
    application: list[dict]

    class Config:
        extra = "forbid"
        
class EntryResponse(BaseModel):
    id: str
    
    class Config:
        extra = "forbid"
        
class SelectRequest(BaseModel):
    id: str
    
    class Config:
        extra = "forbid"