from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.application import ApplicationController
from app.controllers.message import MessageController
from app.controllers.user import UserController
from app.services.application import ApplicationService
from app.services.message import MessageService
import logging

from app.services.user import UserService

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


def get_application_controller_router():
    service = ApplicationService()
    return ApplicationController(service=service).router


def get_message_controller_router():
    service = MessageService()
    return MessageController(service=service).router


def get_user_controller_router():
    service = UserService()
    return UserController(service=service).router


app.include_router(
    get_application_controller_router(), tags=["application"], prefix="/application"
)
app.include_router(get_message_controller_router(), tags=["message"], prefix="/message")
app.include_router(get_user_controller_router(), tags=["user"], prefix="/user")
