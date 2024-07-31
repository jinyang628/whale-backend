from typing import Any, Optional

from app.connectors.orm import Orm
from app.models.stores.user import User, UserORM

orm = Orm(is_user_facing=False)


class UserService:
    async def get(
        self,
        user_id: str,
        user_email: Optional[str] = None,
        fields: Optional[set[str]] = None,
    ) -> Any:
        result: list[User] = await orm.static_get(
            orm_model=UserORM,
            pydantic_model=User,
            filters={
                "boolean_clause": "AND",
                "conditions": [{"column": "id", "operator": "=", "value": user_id}],
            },
        )
        if len(result) < 1:
            if user_email is None:
                raise ValueError(f"User of id {user_id} not found.")
            # User email is only sent during initial fetch at login
            result = await self.post(
                users=[User(id=user_id, email=user_email, applications=[], visits=0)]
            )
        elif len(result) > 1:
            raise ValueError(f"Multiple users found for id {user_id}")
        user: User = result[0]
        if fields:
            user_dict: dict[str, Any] = user.model_dump()
            result: dict[str, Any] = {}
            for key, value in user_dict.items():
                if key in fields:
                    result[key] = value
            return result
        return user

    async def update(
        self,
        filters: dict[str, Any],
        updated_data: Optional[dict[str, Any]],
        increment_field: Optional[str],
    ) -> None:
        await orm.static_update(
            orm_model=UserORM,
            filters=filters,
            updated_data=updated_data,
            increment_field=increment_field,
        )

    async def post(self, users: list[User]) -> list[User]:
        await orm.static_post(
            orm_model=UserORM, data=[user.model_dump() for user in users]
        )
        return users
