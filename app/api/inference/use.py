import logging
import os

import requests
from dotenv import load_dotenv

from app.models.inference.use import UseInferenceRequest, UseInferenceResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


load_dotenv()
BASE_URL = os.getenv("ML_ENDPOINT")
SERVICE_ENDPOINT = "inference/use"


def infer_use(input: UseInferenceRequest) -> UseInferenceResponse:
    try:
        response = requests.post(
            f"{BASE_URL}/{SERVICE_ENDPOINT}", json=input.model_dump()
        )
        response.raise_for_status()
        inference_response = UseInferenceResponse.model_validate(response.json())
        return inference_response
    except requests.RequestException as e:
        log.error(f"Failed to infer response from server: {e}")
        raise e
    except Exception as e:
        log.error(f"Unknown error during inference occurred: {e}")
        raise e
