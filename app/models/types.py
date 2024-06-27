from pydantic import BaseModel

class EntryRequest(BaseModel):
    application: list[dict]

    class Config:
        extra = "forbid"
        
class EntryResponse(BaseModel):
    id: str
    
    class Config:
        extra = "forbid"