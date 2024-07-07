import requests
from dotenv import load_dotenv

import os

import logging

from app.models.inference import InferenceRequest, InferenceResponse

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


load_dotenv()
BASE_URL = os.getenv("ML_ENDPOINT")
SERVICE_ENDPOINT = "inference"


def infer(input: InferenceRequest) -> InferenceResponse:
    try:
        response = requests.post(
            f"{BASE_URL}/{SERVICE_ENDPOINT}", json=input.model_dump()
        )
        response.raise_for_status()
        inference_response = InferenceResponse.model_validate(response.json())
        return inference_response
    except TypeError as e:
        log.error(f"Failed to parse the response for id {input.id} from server: {e}")
        return None
    except requests.RequestException as e:
        log.error(f"Failed to fetch response for id {input.id} from server: {e}")
        return None
    except Exception as e:
        log.error(f"Unknown error for id {input.id} occurred: {e}")
        return None
