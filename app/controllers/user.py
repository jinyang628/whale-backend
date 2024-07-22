import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.exceptions.exception import DatabaseError
from app.models.user import UpdateCacheRequest
from app.services.user import UserService

log = logging.getLogger(__name__)

router = APIRouter()


class UserController:

    def __init__(self, service: UserService):
        self.router = APIRouter()
        self.service = service
        self.setup_routes()

    def setup_routes(self):
        router = self.router
        
        @router.patch("/cache/update")
        async def update_cache(input: UpdateCacheRequest) -> JSONResponse:
            try:
                await self.service.update(
                    filters={"boolean_clause": "AND", "conditions": [{"column": "email", "operator": "=", "value": input.user_email}]},
                    updated_data={"applications": {"applications" : input.applications }}
                )
                return JSONResponse(status_code=200)
            except DatabaseError as e:
                log.error("Database error: %s", str(e))
                raise HTTPException(status_code=500, detail="Database error") from e
            except Exception as e:
                log.error("Unexpected error in application controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e
        