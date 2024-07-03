import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.inference import infer
from app.models.stores.application import Application
from app.models.inference import ApplicationContent, InferenceRequest, InferenceResponse
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
                application_content_lst: list[ApplicationContent] = await self.service.get_application_content_lst(
                    application_names=input.application_names 
                )
                inference_response: InferenceResponse = infer(
                    input=InferenceRequest(
                        applications=application_content_lst,
                        message=input.message,
                        chat_history=input.chat_history
                    )
                )
                result: PostMessageResponse = await self.service.execute_inference_response(
                    inference_response=inference_response
                )
                # return JSONResponse(
                #     status_code=200, content=response.model_dump()
                # )
            except ValidationError as e:
                log.error("Validation error: %s", str(e))
                raise HTTPException(status_code=422, detail="Validation error") from e
            except Exception as e:
                log.error("Unexpected error in application controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail="An unexpected error occurred") from e            