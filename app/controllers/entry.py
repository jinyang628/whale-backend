import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.exceptions.exception import (DatabaseError)
from app.models.types import EntryRequest, EntryResponse, SelectRequest
from app.services.entry import EntryService

log = logging.getLogger(__name__)

router = APIRouter()


class EntryController:

    def __init__(self, service: EntryService):
        self.router = APIRouter()
        self.service = service
        self.setup_routes()

    def setup_routes(self):

        router = self.router

        @router.post("")
        async def post(input: EntryRequest) -> JSONResponse:
            try:
                response: EntryResponse = await self.service.post(
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
                log.error("Unexpected error in entry_controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail="An unexpected error occurred") from e            
        @router.get("/select")
        async def select(input: SelectRequest) -> JSONResponse:
            try:
                is_valid_application: bool = await self.service.select(
                    input=input
                )
                if not is_valid_application:
                    return HTTPException(status_code=404, detail="Application not found")
                return JSONResponse(
                    status_code=200, content={"message": "Application found"}
                )
            except DatabaseError as e:
                log.error("Database error: %s", str(e))
                raise DatabaseError(message=str(e)) from e
            except Exception as e:
                log.error("Unexpected error in entry_controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e

