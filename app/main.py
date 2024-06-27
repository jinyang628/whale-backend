from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.message import MessageController
from app.services.message import MessageService

app = FastAPI()

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


def get_message_controller_router():
    service = MessageService()
    return MessageController(service=service).router


app.include_router(get_message_controller_router(), tags=["message"], prefix="/message")
