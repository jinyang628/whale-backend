import logging
import requests

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.inference import infer
from app.models.inference import ApplicationContent, InferenceRequest, InferenceResponse
from app.models.message import Message, PostMessageRequest, PostMessageResponse, Role
from app.models.reverse import ReverseActionDelete, ReverseActionWrapper
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

        @router.post("/send")
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
                    user_message=Message(
                        role=Role.USER,
                        content=input.message
                    ),
                    chat_history=input.chat_history,
                    reverse_stack=input.reverse_stack,
                    inference_response=inference_response
                )
                print(result)
                return JSONResponse(
                    status_code=200, content=result.model_dump()
                )
            except ValidationError as e:
                log.error("Validation error: %s", str(e))
                raise HTTPException(status_code=422, detail="Validation error") from e
            except requests.RequestException as e:
                log.error(f"Failed to infer response from server: {e}")
                raise HTTPException(status_code=422, detail="Inference error occurred") from e                        
            except Exception as e:
                log.error("Unexpected error in message controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail="An unexpected error occurred") from e  
            
        @router.post("/reverse")
        async def reverse(input: ReverseActionWrapper) -> JSONResponse:
            try:
                print(input)
                print("error")
                await self.service.reverse_inference_response(input=input)
            except ValidationError as e:
                log.error("Validation error: %s", str(e))
                return HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                log.error("Unexpected error in message controller.py: %s", str(e))
                raise HTTPException(status_code=500, detail="An unexpected error occurred") from e
    