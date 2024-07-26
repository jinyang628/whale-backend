import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.exceptions.exception import DatabaseError
from app.models.application import SelectApplicationResponse
from app.models.user import GetCacheResponse, UpdateCacheRequest
from app.services.application import ApplicationService
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
                    filters={
                        "boolean_clause": "AND",
                        "conditions": [
                            {"column": "id", "operator": "=", "value": input.user_id}
                        ],
                    },
                    updated_data={"applications": input.all_application_names},
                    increment_field=None,
                )
                return JSONResponse(
                    status_code=200, content={"message": "Cache updated successfully"}
                )
            except DatabaseError as e:
                log.error("Database error: %s", str(e))
                raise HTTPException(status_code=500, detail="Database error") from e
            except Exception as e:
                log.error("Unexpected error in application controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e

        @router.get("/cache/get")
        async def get_cache(user_id: str, user_email: str) -> JSONResponse:
            try:
                application_names: dict[str, list] = await self.service.get(
                    user_id=user_id,
                    user_email=user_email,
                    fields={"applications"},
                )
                await self.service.update(
                    filters={
                        "boolean_clause": "AND",
                        "conditions": [
                            {"column": "id", "operator": "=", "value": user_id}
                        ],
                    },
                    updated_data=None,
                    increment_field="visits",
                )
                applications: list[SelectApplicationResponse] = []
                for name in application_names["applications"]:
                    response: Optional[SelectApplicationResponse] = (
                        await ApplicationService().select(name=name)
                    )
                    if not response:
                        continue
                    applications.append(response)
                result = GetCacheResponse(applications=applications)
                return JSONResponse(status_code=200, content=result.model_dump())
            except DatabaseError as e:
                log.error("Database error: %s", str(e))
                raise HTTPException(status_code=500, detail="Database error") from e
            except Exception as e:
                log.error("Unexpected error in application controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e
