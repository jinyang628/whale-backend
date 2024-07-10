from typing import Any, Literal
from pydantic import BaseModel, Field

class ReverseAction(BaseModel):
    action_type: str

class Delete(ReverseAction):
    action_type: Literal["delete"] = "delete"
    ids: list[Any]

class Update(ReverseAction):
    action_type: Literal["update"] = "update"
    reverse_updated_data: list[dict[Any, dict]]

class Post(ReverseAction):
    action_type: Literal["post"] = "post"
    deleted_data: list[dict[str, Any]]
    
class Get(ReverseAction):
    action_type: Literal["get"] = "get"

ReverseActionUnion = Delete | Update | Post | Get

class ReverseActionWrapper(BaseModel):
    action: ReverseActionUnion = Field(..., discriminator="action_type")