import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.exceptions.exception import (DatabaseError)
from app.models.types import ApplicationRequest, ApplicationResponse, SelectRequest, SelectResponse
from app.services.application import ApplicationService

log = logging.getLogger(__name__)

router = APIRouter()


class EntryController:

    def __init__(self, service: ApplicationService):
        self.router = APIRouter()
        self.service = service
        self.setup_routes()

    def setup_routes(self):

        router = self.router

        @router.post("")
        async def post(input: ApplicationRequest) -> JSONResponse:
            try:
                response: ApplicationResponse = await self.service.post(
                    input=input
                )
                return JSONResponse(
                    status_code=200, content=response.model_dump()
                )
            except ValidationError as e:
                log.error("Validation error: %s", str(e))
                raise HTTPException(status_code=422, detail="Validation error") from e
            except DatabaseError as e:
                log.error("Database error: %s", str(e))
                raise HTTPException(status_code=500, detail="Database error") from e
            except Exception as e:
                log.error("Unexpected error in applicaion controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail="An unexpected error occurred") from e            
            
               
        @router.get("/select")
        async def select(input: SelectRequest) -> JSONResponse:
            try:
                response: Optional[SelectResponse] = await self.service.select(
                    input=input
                )
                if not response:
                    return HTTPException(status_code=404, detail="Application not found")
                return JSONResponse(
                    status_code=200, content=response.model_dump()
                )
            except DatabaseError as e:
                log.error("Database error: %s", str(e))
                raise HTTPException(status_code=500, detail="Database error") from e
            except Exception as e:
                log.error("Unexpected error in application controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e

