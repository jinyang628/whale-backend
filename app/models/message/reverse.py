from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.application.base import Table


class ReverseAction(BaseModel):
    action_type: str


class ReverseActionDelete(ReverseAction):
    action_type: Literal["delete"] = "delete"
    ids: list[Any]
    target_table: Table
    application_name: str

    class Config:
        arbitrary_types_allowed = True


class ReverseActionUpdate(ReverseAction):
    action_type: Literal["update"] = "update"
    reverse_filter_conditions: dict[str, Any]
    reverse_updated_data: dict[str, Any]
    target_table: Table
    application_name: str

    class Config:
        arbitrary_types_allowed = True


class ReverseActionPost(ReverseAction):
    action_type: Literal["post"] = "post"
    deleted_data: list[dict[str, Any]]
    target_table: Table
    application_name: str

    class Config:
        arbitrary_types_allowed = True


class ReverseActionGet(ReverseAction):
    action_type: Literal["get"] = "get"


class ReverseActionClarification(ReverseAction):
    action_type: Literal["clarification"] = "clarification"


ReverseActionUnion = (
    ReverseActionDelete
    | ReverseActionUpdate
    | ReverseActionPost
    | ReverseActionGet
    | ReverseActionClarification
)


class ReverseActionWrapper(BaseModel):
    action: ReverseActionUnion = Field(..., discriminator="action_type")
