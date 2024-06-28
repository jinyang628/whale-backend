import json
from app.models.stores.base import BaseObject
from app.models.utils import generate_identifier, sql_value_to_typed_value
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base 
from sqlalchemy.sql import func

Base = declarative_base()

# Update this version accordingly
ENTRY_VERSION: int = 1

class ApplicationORM(Base):
    __tablename__ = "application"
    
    id = Column(String, primary_key=True)
    version = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    tables = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())  # Automatically use the current timestamp of the database server upon creation
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())  # Automatically use the current timestamp of the database server upon creation and update
    
class Application(BaseObject):
    version: int
    name: str
    tables: str

    @classmethod
    def local(
        cls,
        name: str,
        tables: list[dict],
    ):
        return Application(
            id=generate_identifier(Application.generate_id(
                version=ENTRY_VERSION, 
                name=name,
                tables=tables
            )),
            version=ENTRY_VERSION,
            name=name,
            tables=json.dumps(tables),
        )
        


    @classmethod
    def remote(
        cls,
        **kwargs,
    ):
        return cls(
            id=sql_value_to_typed_value(dict=kwargs, key="id", type=str),
            version=sql_value_to_typed_value(dict=kwargs, key="version", type=int),
            name=sql_value_to_typed_value(dict=kwargs, key="name", type=str),
            tables=sql_value_to_typed_value(dict=kwargs, key="tables", type=str),
        )
