from pydantic import BaseModel


class UpdateCacheRequest(BaseModel):
    user_email: str
    applications: list[str]