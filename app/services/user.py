from typing import Any, Optional
from app.connectors.orm import Orm
from app.models.stores.user import User, UserORM


class UserService:
    
    async def get(self, user_email: str, fields: Optional[set[str]] = None) -> Any:
        orm = Orm(is_user_facing=False)
        result: list[User] = await orm.static_get(
        orm_model=UserORM, 
        pydantic_model=User, 
            filters={"boolean_clause": "AND", "conditions": [{"column": "email", "operator": "=", "value": user_email}]}
        )
        if len(result) < 1:
            raise ValueError(f"User of email {user_email} not found.")
        if len(result) > 1:
            raise ValueError(f"Multiple users found for email {user_email}")
        user: User = result[0]
        if fields:
            user_dict: dict[str, Any] = user.model_dump()
            result: dict[str, Any] = {}
            for key, value in user_dict.items():
                if key in fields:
                    result[key] = value            
            return result
        return user
    
    async def update(self, filters: dict[str, Any], updated_data: dict[str, Any]):
        orm = Orm(is_user_facing=False)
        await orm.static_update(
            orm_model=UserORM, 
            filters=filters, 
            updated_data=updated_data
        )