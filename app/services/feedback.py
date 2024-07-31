from app.connectors.orm import Orm
from app.models.stores.feedback import Feedback, FeedbackORM


class FeedbackService:
    async def post(self, id: str, name: str, email: str, feedback: str):
        orm = Orm(is_user_facing=False)
        await orm.static_post(
            orm_model=FeedbackORM,
            data=[
                Feedback.local(
                    user_id=id, name=name, email=email, feedback=feedback
                ).model_dump()
            ],
        )
