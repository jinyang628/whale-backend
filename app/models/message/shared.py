from enum import StrEnum
from typing import Any, Optional
from pydantic import BaseModel

class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: Role
    content: str
    blocks: Optional[list[dict[str, Any]]] = None