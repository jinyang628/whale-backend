import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.exceptions.exception import DatabaseError
from app.models.application.base import ApplicationContent
from app.models.application.build import PostApplicationResponse
from app.models.application.select import (
    SelectApplicationRequest,
    SelectApplicationResponse,
)
from app.models.application.validate import ValidateResponse
from app.services.application import ApplicationService

log = logging.getLogger(__name__)

router = APIRouter()


class ApplicationController:

    def __init__(self, service: ApplicationService):
        self.router = APIRouter()
        self.service = service
        self.setup_routes()

    def setup_routes(self):

        router = self.router

        @router.post("/build")
        async def build(input: ApplicationContent) -> JSONResponse:
            try:
                response: PostApplicationResponse = await self.service.build(
                    application_content=input
                )
                await self.service.generate_client_application(
                    application_content=input
                )
                return JSONResponse(status_code=200, content=response.model_dump())
            except ValidationError as e:
                log.error("Validation error in application controller: %s", str(e))
                raise HTTPException(status_code=422, detail="Validation error") from e
            except DatabaseError as e:
                log.error("Database error in application controller: %s", str(e))
                raise HTTPException(status_code=500, detail="Database error") from e
            except Exception as e:
                log.error("Unexpected error in application controller.py: %s", str(e))
                raise HTTPException(
                    status_code=500, detail="An unexpected error occurred"
                ) from e

        @router.get("/validate")
        async def validate(name: str) -> JSONResponse:
            try:
                response: Optional[SelectApplicationResponse] = (
                    await self.service.select(name=name)
                )
                if not response:
                    return JSONResponse(
                        status_code=200,
                        content=ValidateResponse(is_unique=True).model_dump(),
                    )
                return JSONResponse(
                    status_code=200,
                    content=ValidateResponse(is_unique=False).model_dump(),
                )
            except ValidationError as e:
                log.error("Validation error in application controller: %s", str(e))
                raise HTTPException(status_code=422, detail="Validation error") from e
            except DatabaseError as e:
                log.error("Database error in application controller: %s", str(e))
                raise HTTPException(status_code=500, detail="Database error") from e
            except Exception as e:
                log.error("Unexpected error in application controller.py: %s", str(e))
                raise HTTPException(
                    status_code=500, detail="An unexpected error occurred"
                ) from e

        @router.post("/select")
        async def select(input: SelectApplicationRequest) -> JSONResponse:
            try:
                response: Optional[SelectApplicationResponse] = (
                    await self.service.select(name=input.new_application_name)
                )
                if not response:
                    return HTTPException(
                        status_code=404, detail="Application not found"
                    )
                input.all_application_names.append(input.new_application_name)
                
                # Only insert into cache if user is logged in
                if input.user_id:
                    await self.service.insert_cache(
                        names=input.all_application_names, user_id=input.user_id
                    )
                    
                return JSONResponse(status_code=200, content=response.model_dump())
            except DatabaseError as e:
                log.error("Database error: %s", str(e))
                raise HTTPException(status_code=500, detail="Database error") from e
            except Exception as e:
                log.error("Unexpected error in application controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e
