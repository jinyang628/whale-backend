from pydantic import BaseModel
import uuid

class BaseObject(BaseModel):
    id: uuid.UUID = None
    
    class Config:
        orm_mode = True
        from_attributes = True

    @staticmethod
    def generate_id() -> uuid.UUID:
        return uuid.uuid4()