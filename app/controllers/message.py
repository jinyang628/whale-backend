import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.inference import infer
from app.models.stores.application import Application
from app.models.inference import ApplicationContent, InferenceRequest
from app.models.message import PostMessageRequest, PostMessageResponse
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
        async def post(input: PostMessageRequest) -> JSONResponse:
            try:
                applications: list[Application] = await self.service.get_applications(
                    application_ids=input.application_ids 
                )
                application_content_lst: list[ApplicationContent] = [
                    ApplicationContent(
                        name=application.name,
                        tables=application.tables
                    )    
                    for application in applications
                ]
                response: PostMessageResponse = infer(
                    input=InferenceRequest(
                        applications=application_content_lst,
                        message=input.message,
                        chat_history=input.chat_history
                    )
                )
                # return JSONResponse(
                #     status_code=200, content=response.model_dump()
                # )
            except ValidationError as e:
                log.error("Validation error: %s", str(e))
                raise HTTPException(status_code=422, detail="Validation error") from e
            except Exception as e:
                log.error("Unexpected error in applicaion controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail="An unexpected error occurred") from e            