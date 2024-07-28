from enum import StrEnum
from pydantic import BaseModel
from abc import ABC

class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel, ABC):
    role: Role
    content: str
