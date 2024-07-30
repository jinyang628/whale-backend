from pydantic import BaseModel

from app.models.application.select import SelectApplicationResponse


class UpdateCacheRequest(BaseModel):
    user_id: str
    all_application_names: list[str]


class GetCacheResponse(BaseModel):
    applications: list[SelectApplicationResponse]
