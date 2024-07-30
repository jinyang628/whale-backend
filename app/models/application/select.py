from pydantic import BaseModel

from app.models.application.base import ApplicationContent


class SelectApplicationRequest(BaseModel):
    user_id: str
    new_application_name: str
    all_application_names: list[str]


class SelectApplicationResponse(BaseModel):
    application: ApplicationContent

    class Config:
        extra = "forbid"
