import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.exceptions.exception import (DatabaseError, PipelineError,
                                      UsageLimitExceededError)
from app.models.types import EntryRequest, EntryResponse
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
            print(input)
            try:
                response: str = await self.service.post(
                    input=input
                )
                return JSONResponse(
                    status_code=200, content=response
                )
            except DatabaseError as e:
                log.error("Database error: %s", str(e))
                raise DatabaseError(message=str(e)) from e
            except Exception as e:
                log.error("Unexpected error in entry_controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail=str(e)) from e
