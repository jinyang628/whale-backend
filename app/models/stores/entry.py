from app.models.stores.base import BaseObject
from app.models.utils import generate_identifier, sql_value_to_typed_value
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base 
from sqlalchemy.sql import func

Base = declarative_base()

# Update this version accordingly
ENTRY_VERSION: int = 1

class EntryORM(Base):
    __tablename__ = "entry"
    
    id = Column(String, primary_key=True)
    version = Column(Integer, nullable=False)
    application = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())  # Automatically use the current timestamp of the database server upon creation
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())  # Automatically use the current timestamp of the database server upon creation and update
    
class Entry(BaseObject):
    version: int
    application: str

    @classmethod
    def local(
        cls,
        application: str,
    ):
        return Entry(
            id=generate_identifier(Entry.generate_id(
                version=ENTRY_VERSION, 
                application=application
            )),
            version=ENTRY_VERSION,
            application=application
        )

    @classmethod
    def remote(
        cls,
        **kwargs,
    ):
        return cls(
            id=sql_value_to_typed_value(dict=kwargs, key="id", type=str),
            version=sql_value_to_typed_value(dict=kwargs, key="version", type=int),
            application=sql_value_to_typed_value(dict=kwargs, key="url", type=str),
        )
