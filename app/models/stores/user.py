import logging

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

from app.models.utils import sql_value_to_typed_value

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

Base = declarative_base()


class UserORM(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True)
    email = Column(String, nullable=False)
    applications = Column(ARRAY(String), nullable=False)
    visits = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )
    total_calls = Column(Integer, nullable=False, default=0)


class User(BaseModel):
    id: str
    email: str
    applications: list[str]
    visits: int
    total_calls: int

    @classmethod
    def local(
        cls,
        id: str,
        email: str,
        applications: list[str],
        visits: int,
        total_calls: int,
    ):
        return User(
            id=id,
            email=email,
            applications=applications,
            visits=visits,
            total_calls=total_calls,
        )

    @classmethod
    def remote(
        cls,
        **kwargs,
    ):
        return cls(
            id=sql_value_to_typed_value(dict=kwargs, key="id", type=str),
            email=sql_value_to_typed_value(dict=kwargs, key="email", type=str),
            applications=sql_value_to_typed_value(
                dict=kwargs, key="applications", type=list[str]
            ),
            visits=sql_value_to_typed_value(dict=kwargs, key="visits", type=int),
            total_calls=sql_value_to_typed_value(
                dict=kwargs, key="total_calls", type=int
            ),
        )
