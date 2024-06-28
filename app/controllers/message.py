import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.models.types import MessageRequest, MessageResponse
from app.services.message import MessageService

log = logging.getLogger(__name__)

router = APIRouter()


class MessageController:

    def __init__(self, service: MessageService):
        self.router = APIRouter()
        self.service = service
        self.setup_routes()

    def setup_routes(self):

        router = self.router

        @router.post("")
        async def post(input: MessageRequest) -> JSONResponse:
            try:
                print("message controller.py")
                print(input)
                # response: ApplicationResponse = await self.service.post(
                #     input=input
                # )
                # return JSONResponse(
                #     status_code=200, content=response.model_dump()
                # )
            except ValidationError as e:
                log.error("Validation error: %s", str(e))
                raise HTTPException(status_code=422, detail="Validation error") from e
            except Exception as e:
                log.error("Unexpected error in applicaion controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail="An unexpected error occurred") from e            