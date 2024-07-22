from typing import Any
from app.models.stores.base import BaseObject
from app.models.utils import sql_value_to_typed_value
from sqlalchemy import JSON, Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import declarative_base 
from sqlalchemy.sql import func
import logging

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

Base = declarative_base()

class UserORM(Base):
    __tablename__ = "user"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String, nullable=False)
    applications = Column(ARRAY(String), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
class User(BaseObject):
    email: str
    applications: list[str]

    @classmethod
    def local(
        cls,
        email: str,
        applications: list[str],
    ):
        return User(
            id=User.generate_id(),
            email=email,
            applications=applications,
        )

    @classmethod
    def remote(
        cls,
        **kwargs,
    ):
        return cls(
            id=sql_value_to_typed_value(dict=kwargs, key="id", type=str),
            applications=sql_value_to_typed_value(dict=kwargs, key="applications", type=list[str]),
        )
