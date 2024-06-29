from enum import StrEnum
from pydantic import BaseModel
from typing import Optional

class DataType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    
class Column(BaseModel):
    name: str
    data_type: DataType
    nullable: bool = False

class Table(BaseModel):
    name: str
    description: Optional[str] = None
    columns: list[Column]

class ApplicationContent(BaseModel):
    name: str
    tables: list[Table]
    
    class Config: 
        extra = "forbid"
        

    
class PostApplicationRequest(ApplicationContent):
    pass
        
class PostApplicationResponse(BaseModel):
    id: str
    
    class Config:
        extra = "forbid"
        
class SelectApplicationRequest(BaseModel):
    id: str
    
    class Config:
        extra = "forbid"
     
class SelectApplicationResponse(BaseModel):
    name: str
    
    class Config:
        extra = "forbid"   