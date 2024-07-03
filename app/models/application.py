from enum import StrEnum
import uuid
from pydantic import BaseModel
from typing import Optional


class DataType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"


# TODO: Add more types, e.g. UUID, etc. Will handle the id generation in house in server
class PrimaryKey(StrEnum):
    NONE = "none"
    AUTO_INCREMENT = "auto_increment"


class Column(BaseModel):
    name: str
    data_type: DataType
    nullable: bool = False
    primary_key: PrimaryKey = PrimaryKey.NONE


class Table(BaseModel):
    name: str
    description: Optional[str] = None
    columns: list[Column]

    def __init__(self, **data):
        super().__init__(**data)
        self._validate_primary_key()

    def _validate_primary_key(self):
        primary_key_columns = [
            col for col in self.columns if col.primary_key != PrimaryKey.NONE
        ]
        if len(primary_key_columns) != 1:
            raise ValueError("Exactly one column must be set as primary key.")


class ApplicationContent(BaseModel):
    name: str
    tables: list[Table]

    class Config:
        extra = "forbid"


class PostApplicationRequest(ApplicationContent):
    pass


class PostApplicationResponse(BaseModel):
    name: str

    class Config:
        extra = "forbid"


class SelectApplicationRequest(BaseModel):
    name: str

    class Config:
        extra = "forbid"


class SelectApplicationResponse(BaseModel):
    name: str

    class Config:
        extra = "forbid"
