from pydantic import BaseModel

class EntryInput(BaseModel):
    application: str

    class Config:
        extra = "forbid"
        
class EntryResponse(BaseModel):
    id: str
    
    class Config:
        extra = "forbid"