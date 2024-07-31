import logging

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.api.inference.create import infer_create
from app.api.inference.use import infer_use
from app.models.inference.create import CreateInferenceRequest, CreateInferenceResponse
from app.models.inference.use import (
    ApplicationContent,
    UseInferenceRequest,
    UseInferenceResponse,
)
from app.models.message.create import CreateMessage, CreateRequest, CreateResponse
from app.models.message.reverse import ReverseActionWrapper
from app.models.message.shared import Role
from app.models.message.use import UseMessage, UseRequest, UseResponse
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

        @router.post("/use")
        async def use(input: UseRequest) -> JSONResponse:
            try:
                application_content_lst: list[ApplicationContent] = (
                    await self.service.get_application_content_lst(
                        application_names=input.application_names
                    )
                )
                log.info(f"Application content list: {application_content_lst}")
                inference_response: UseInferenceResponse = infer_use(
                    input=UseInferenceRequest(
                        applications=application_content_lst,
                        message=input.message,
                        chat_history=input.chat_history,
                    )
                )
                log.info(f"Inference response: {inference_response}")
                result: UseResponse = await self.service.execute_inference_response(
                    user_message=UseMessage(role=Role.USER, content=input.message),
                    chat_history=input.chat_history,
                    reverse_stack=input.reverse_stack,
                    inference_response=inference_response,
                    user_id=input.user_id,
                )
                log.info(f"Returning result to frontend: {result.model_dump()}")
                return JSONResponse(status_code=200, content=result.model_dump())
            except ValidationError as e:
                log.error("Validation error: %s", str(e))
                raise HTTPException(status_code=422, detail="Validation error") from e
            except requests.RequestException as e:
                log.error(f"Failed to infer response from server: {e}")
                raise HTTPException(
                    status_code=422, detail="Inference error occurred"
                ) from e
            except Exception as e:
                log.error("Unexpected error in message controller.py: %s", str(e))
                raise HTTPException(
                    status_code=500, detail="An unexpected error occurred"
                ) from e

        @router.post("/create")
        async def create(input: CreateRequest) -> JSONResponse:
            try:
                inference_response: CreateInferenceResponse = infer_create(
                    input=CreateInferenceRequest(
                        message=input.message,
                        chat_history=input.chat_history,
                    )
                )
                result: CreateResponse = await self.service.construct_create_response(
                    user_message=CreateMessage(role=Role.USER, content=input.message),
                    chat_history=input.chat_history,
                    overview=inference_response.overview,
                    clarification=inference_response.clarification,
                    concluding_message=inference_response.concluding_message,
                    application_content=inference_response.application_content,
                )
                log.info(f"Returning result to frontend: {result.model_dump()}")
                return JSONResponse(status_code=200, content=result.model_dump())
            except ValidationError as e:
                log.error("Validation error: %s", str(e))
                raise HTTPException(status_code=422, detail="Validation error") from e
            except requests.RequestException as e:
                log.error(f"Failed to infer response from server: {e}")
                raise HTTPException(
                    status_code=422, detail="Inference error occurred"
                ) from e
            except Exception as e:
                log.error("Unexpected error in message controller.py: %s", str(e))
                raise HTTPException(
                    status_code=500, detail="An unexpected error occurred"
                ) from e

        @router.post("/reverse")
        async def reverse(input: ReverseActionWrapper) -> JSONResponse:
            try:
                await self.service.reverse_inference_response(input=input)
                return JSONResponse(status_code=200, content={"message": "Success"})
            except ValidationError as e:
                log.error("Validation error: %s", str(e))
                return HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                log.error("Unexpected error in message controller.py: %s", str(e))
                raise HTTPException(
                    status_code=500, detail="An unexpected error occurred"
                ) from e
