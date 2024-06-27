from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.entry import EntryController
from app.services.entry import EntryService

app = FastAPI()

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


def get_entry_controller_router():
    service = EntryService()
    return EntryController(service=service).router


app.include_router(get_entry_controller_router(), tags=["entry"], prefix="/entry")
