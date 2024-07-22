import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.exceptions.exception import DatabaseError
from app.models.application import (
    PostApplicationRequest,
    PostApplicationResponse,
    SelectApplicationRequest,
    SelectApplicationResponse,
)
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

        @router.post("")
        async def post(input: PostApplicationRequest) -> JSONResponse:
            try:
                response: PostApplicationResponse = await self.service.post(input=input)
                await self.service.generate_client_application(input=input)
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

        @router.post("/select")
        async def select(input: SelectApplicationRequest) -> JSONResponse:
            try:
                response: Optional[SelectApplicationResponse] = (
                    await self.service.select(name=input.name)
                )
                if not response:
                    return HTTPException(
                        status_code=404, detail="Application not found"
                    )
                await self.service.insert_cache(
                    name=input.name, user_email=input.user_email
                )
                return JSONResponse(status_code=200, content=response.model_dump())
            except DatabaseError as e:
                log.error("Database error: %s", str(e))
                raise HTTPException(status_code=500, detail="Database error") from e
            except Exception as e:
                log.error("Unexpected error in application controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e

        @router.post("/gpt")
        async def gpt(gpt: PostApplicationRequest) -> JSONResponse:
            print(gpt)
