import logging

from pydantic import BaseModel
from sqlalchemy import UUID, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

from app.models.stores.base import BaseObject
from app.models.utils import sql_value_to_typed_value

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

Base = declarative_base()


class FeedbackORM(Base):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    feedback = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )


class Feedback(BaseObject):
    user_id: str
    name: str
    email: str
    feedback: str

    @classmethod
    def local(cls, user_id: str, name: str, email: str, feedback: str):
        return Feedback(
            id=Feedback.generate_id(),
            user_id=user_id,
            name=name,
            email=email,
            feedback=feedback,
        )

    @classmethod
    def remote(
        cls,
        **kwargs,
    ):
        return cls(
            id=sql_value_to_typed_value(dict=kwargs, key="id", type=str),
            user_id=sql_value_to_typed_value(dict=kwargs, key="user_id", type=str),
            name=sql_value_to_typed_value(dict=kwargs, key="name", type=str),
            email=sql_value_to_typed_value(dict=kwargs, key="email", type=str),
            feedback=sql_value_to_typed_value(dict=kwargs, key="feedback", type=str),
        )
