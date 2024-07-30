from pydantic import BaseModel


class ValidateRequest(BaseModel):
    name: str

class ValidateResponse(BaseModel):
    is_unique: bool