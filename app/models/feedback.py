from pydantic import BaseModel


class FeedbackRequest(BaseModel):
    id: str
    name: str
    email: str
    feedback: str
