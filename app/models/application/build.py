from pydantic import BaseModel

from app.models.application.base import ApplicationContent


class PostApplicationRequest(ApplicationContent):
    pass


class PostApplicationResponse(BaseModel):
    name: str

    class Config:
        extra = "forbid"