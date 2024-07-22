from pydantic import BaseModel

from app.models.application import SelectApplicationResponse


class UpdateCacheRequest(BaseModel):
    user_email: str
    applications: list[str]
    
class GetCacheResponse(BaseModel):
    applications: list[SelectApplicationResponse]