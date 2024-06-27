import logging
import os

from dotenv import find_dotenv, load_dotenv

from app.connectors.orm import Orm
from app.models.stores.entry import Entry
from app.models.types import EntryRequest

log = logging.getLogger(__name__)

load_dotenv(find_dotenv(filename=".env"))
TURSO_DB_URL = os.environ.get("TURSO_DB_URL")
TURSO_DB_AUTH_TOKEN = os.environ.get("TURSO_DB_AUTH_TOKEN")

class EntryService:
    
    async def post(self, input: EntryRequest) -> str:
        """Inserts the entry into the entry table."""
        entry = Entry.local(application=input.application)
        orm = Orm(url=TURSO_DB_URL, auth_token=TURSO_DB_AUTH_TOKEN)
        orm.insert(models=[entry])
        return entry.id

    ###
    ### Main pipeline logic
    ###
    # async def start_entry_process(self, input: EntryDbInput) -> BrainResponse:
    #     """Main function that controls the overall flow of the business logic in the pre-inference part of the pipeline."""
    #     is_within_limit: bool = await self.is_within_limit(api_key=input.api_key)
    #     if not is_within_limit:
    #         log.error(f"Usage limit exceeded {USAGE_LIMIT}")
    #         raise UsageLimitExceededError(
    #             message=f"Usage limit exceeded {USAGE_LIMIT}"
    #         )
    #     print("error")
    #     jsonified_conversation: dict[str, str] = await self.extract_url_content(
    #         url=input.url
    #     )
    #     inference_input = InferenceInput(
    #         conversation=jsonified_conversation, 
    #         content=input.content
    #     )
    #     try:
    #         result: BrainResponse = await self.infer(data=inference_input)
    #     except PipelineError as e:
    #         log.error(
    #             "Error posting infer request to BRAIN in entry_service.py: %s",
    #             str(e),
    #         )
    #         raise e
    #     except Exception as e:
    #         log.error(
    #             "Unexpected error while posting infer request to BRAIN in entry_service.py: %s",
    #         )
    #         raise e

    #     # Only post to entry db/increment usage if inference is successful
    #     try:
    #         log.info(
    #             f"Token length: {result.token_sum} has been consumed by the user"
    #         )
    #         entry_id: str = await self.post_entry_and_increment_usage(
    #             input=input, token_sum=result.token_sum
    #         )
    #     except DatabaseError as e:
    #         log.error(
    #             "Error posting to entry db/incrementing usage in entry_service.py: %s",
    #             str(e),
    #         )
    #         raise e
    #     except Exception as e:
    #         log.error(
    #             "Unexpected error while posting to entry db/incrementing usage in entry_service.py: %s",
    #             str(e),
    #         )
    #         raise e

    #     inference_db_input: list[InferenceDbInput] = (
    #         self.prepare_inference_db_input_lst(
    #             entry_id=entry_id,
    #             conversation=jsonified_conversation,
    #             result=result,
    #         )
    #     )

    #     try:
    #         await InferenceService().post(data=inference_db_input)
    #     except DatabaseError as e:
    #         log.error(
    #             "Error posting to inference db in entry_service.py: %s",
    #             str(e),
    #         )
    #         raise e
    #     except Exception as e:
    #         log.error(
    #             "Unexpected error while posting to inference db in entry_service.py: %s",
    #             str(e),
    #         )
    #         raise e
        
    #     log.info(f"Result to be returned to fingers: {result}")
    #     return result

    # async def post_entry_and_increment_usage(
    #     self, input: EntryDbInput, token_sum: int
    # ) -> str:
    #     """Posts the entry to the entry db and increments the usage of the user upon successful inference.

    #     Args:
    #         input (EntryDbInput): The input data to be stored in the entry table
    #         token_sum (int): The token sum consumed by the user in this inference call

    #     Returns:
    #         str: The entry_id of the entry posted to the entry db, which will be a foreign key in the inference table
    #     """
    #     try:
    #         increment_usage_task = asyncio.create_task(
    #            UserService().increment_usage(
    #                 api_key=input.api_key, token_sum=token_sum
    #             )
    #         )
    #         post_task = asyncio.create_task(
    #             self.post(data=[input], return_column="entry_id")
    #         )

    #         await increment_usage_task
    #         entry_ids = await post_task

    #         return entry_ids[0]
    #     except DatabaseError as e:
    #         log.error(
    #             "Error incrementing usage/posting to entry db in entry_service.py: %s",
    #             str(e),
    #         )
    #         raise e
    #     except Exception as e:
    #         log.error(
    #             "Unexpected error while incrementing usage/posting to entry db in entry_service.py: %s",
    #             str(e),
    #         )
    #         raise e

    # ###
    # ### DB logic
    # ###
    # async def is_within_limit(self, api_key: str) -> bool:
    #     """Checks if the user has reached the usage limit.

    #     Args:
    #         api_key (str): The API key of the user

    #     Returns:
    #         bool: True if the user has not reached the usage limit, False otherwise
    #     """

    #     try:
    #         is_within_limt: bool = UserService().is_within_limit(api_key=api_key)
    #         return is_within_limt
    #     except DatabaseError as e:
    #         log.error(
    #             "Error checking usage limit in entry_service.py: %s",
    #         )
    #         raise e
    #     except Exception as e:
    #         log.error(
    #             "Unexpected error while checking usage limit in entry_servie.py: %s",
    #             str(e),
    #         )
    #         raise e

    ###
    ### API logic
    ###
    # async def infer(self, data: InferenceInput) -> BrainResponse:
    #     """Sends a POST request to the Brain for inference and
    #     returns a dictionary containing the results of the respective
    #     tasks chosen.

    #     Args:
    #         data (InferenceInput): The entry to be sent for inference
    #     """

    #     try:
    #         if not BRAIN_API_URL:
    #             raise ValueError("BRAIN_API_URL is not set in .env file.")
    #         url: str = f"{BRAIN_API_URL}/inference"

    #         data_dict = data.model_dump()

    #         # Make a POST request to the Brain repo, set a generous timeout of 5 minutes
    #         async with httpx.AsyncClient(timeout=300.0) as client:
    #             log.info(f"Data sent to Brain: {data_dict}")
    #             response = await client.post(url, json=data_dict)
    #             if response.status_code != 200:
    #                 log.error(
    #                     f"Inference API call failed with status code {response.status_code}, response: {response.text}"
    #                 )
    #                 raise PipelineError(message="Failed to complete inference")
    #             brain_response: BrainResponse = BrainResponse(**response.json())
    #             return brain_response
    #     except PipelineError as e:
    #         raise e
    #     except json.JSONDecodeError as e:
    #         log.error(f"JSON decoding error: {e}")
    #         raise e
    #     except Exception as e:
    #         log.error(f"Unexpected error in infer: {e}")
    #         raise e

    # ###
    # ### Business logic
    # ###
    # def validate_tasks(self, tasks: list[str]) -> list[Task]:
    #     """Validates task_str is part of enum value

    #     Args:
    #         tasks (list[str]): The values of the tasks which are sent from Fingers

    #     Raises:
    #         HTTPException: If the task_str is not part of the enum value
    #     """
    #     converted_tasks: list[Task] = []
    #     for task_str in tasks:
    #         if task_str not in Task._value2member_map_:
    #             raise HTTPException(status_code=400, detail=f"Invalid task: {task_str}")
    #         converted_tasks.append(Task(task_str))
    #     return converted_tasks

    # async def extract_url_content(self, url: str) -> dict[str, str]:
    #     """Extracts the title and conversation messages from the ShareGPT url provided.

    #     Args:
    #         url (str): The ShareGPT url to extract content from.

    #     Raises:
    #         ValueError: If the expected tags are not found in the HMTL content
    #     """
    #     async with httpx.AsyncClient(follow_redirects=True) as client:
    #         print("help")
    #         response = await client.get(url)
    #     response.raise_for_status()

    #     soup = BeautifulSoup(response.text, "html.parser")
    #     script_tag = soup.find("script", {"id": "__NEXT_DATA__"})

    #     if not script_tag:
    #         raise ValueError("No script_tag found in the HTML content from url")

    #     try:
    #         json_data: dict[str, any] = json.loads(script_tag.string)
    #     except json.JSONDecodeError as e:
    #         raise ValueError("Invalid JSON in script_tag") from e

    #     props: dict[str, any] = json_data.get("props")
    #     if not props:
    #         raise ValueError("No props found in json_data")

    #     page_props: dict[str, any] = props.get("pageProps")
    #     if not page_props:
    #         raise ValueError("No pageProps found in props")

    #     server_response: dict[str, any] = page_props.get("serverResponse")
    #     if not server_response:
    #         raise ValueError("No serverResponse found in pageProps")

    #     data: dict[str, any] = server_response.get("data")
    #     if not data:
    #         raise ValueError("No data found in serverResponse")

    #     title: str = data.get("title")
    #     if not title:
    #         log.error("No title found in data. Probably because the conversation is cut short by the user and the title is not set.")
    #         title = "Chatlog"

    #     linear_conversation: List[dict[str, str]] = data.get("linear_conversation")
    #     if not linear_conversation:
    #         raise ValueError("No linear_conversation found in data")

    #     conversation: Conversation = None
    #     curr_message: Message = None
    #     for container in linear_conversation:

    #         message: dict[str, any] = container.get("message")
    #         # This is not an error as the message can be empty
    #         if not message:
    #             continue

    #         content: dict[str, any] = message.get("content")
    #         if not content:
    #             raise ValueError("No content found in message")

    #         desired_content: str = ""
    #         if content.get("content_type") == "text":
    #             parts: list[str] = content.get("parts")
    #             if not parts:
    #                 raise ValueError(
    #                     "No parts found in content when content_type is text"
    #                 )
    #             if len(parts) == 0:
    #                 raise ValueError("Empty parts found in content")
    #             # TODO: IS THIS ALWAYS TRUE?
    #             desired_content = parts[0]
    #         elif content.get("content_type") == "code":
    #             # Code messages are what ChatGPT runs on its own server, not important for the conversation
    #             continue
    #         elif content.get("content_type") == "execution_output":
    #             # Execution Output messages are what ChatGPT runs on its own server, not important for the conversation
    #             continue
    #         elif content.get("content_type") == "model_editable_context":
    #             # Not useful content 
    #             continue
    #         elif content.get("content_type") == "tether_browsing_display":
    #             # Not useful content 
    #             continue
    #         elif content.get("content_type") == "tether_quote":
    #             # Not useful content
    #             continue
    #         else:
    #             raise ValueError(
    #                 "Unforseen content_type found in content. Please review the extraction strategy."
    #             )

    #         author: dict[str, any] = message.get("author")
    #         if not author:
    #             raise ValueError("No author found in message")

    #         role: str = author.get("role")
    #         if not role:
    #             raise ValueError("No role found in author")
    #         if role == "system":
    #             # For now, system messages are not relevant for ShareGPT conversations
    #             continue

    #         try:
    #             role_enum: ShareGpt = ShareGpt(role)
    #         except ValueError as e:
    #             raise ValueError("Invalid role found in author") from e

    #         message: Message = None
    #         if role_enum == ShareGpt.USER:
    #             message = UserMessage(
    #                 content=desired_content,
    #                 prev_message=curr_message,
    #                 next_message=None,
    #             )
    #         elif role_enum == ShareGpt.ASSISTANT:
    #             message = AssistantMessage(
    #                 content=desired_content,
    #                 prev_message=curr_message,
    #                 next_message=None,
    #             )

    #         if curr_message:
    #             curr_message.next_message = message
    #             message.prev_message = curr_message
    #         else:
    #             # Keep track of the first message in the Conversation class
    #             conversation = Conversation(title=title, curr_message=message)
    #         curr_message = message

    #     # Uncomment this to see the prettified conversation
    #     # pretty_json: str = json.dumps(conversation.jsonify(), indent=4)
    #     # print(pretty_json)

    #     return conversation.jsonify()

    # def prepare_inference_db_input_lst(
    #     self, 
    #     entry_id: str, 
    #     conversation: dict[str, str], 
    #     result: BrainResponse
    # ) -> list[InferenceDbInput]:
    #     """Prepares the input to be stored in the inference table.

    #     Args:
    #         entry_id (str): The foreign key of the entry table
    #         conversation (dict[str, str]): The conversation extracted from the ShareGPT url
    #         result (BrainResponse): The result of the inference
    #     """
    #     inference_db_input_lst: list[InferenceDbInput] = []

    #     result_lst: list[dict[str, Any]] = result.result
    #     if result_lst:
    #         for i in range(len(result_lst)):
    #             inference_db_input_lst.append(
    #                 InferenceDbInput(
    #                     entry_id=entry_id,
    #                     conversation=json.dumps(conversation),
    #                     result=json.dumps(result.result[i]),
    #                 )
    #             )
    #         return inference_db_input_lst
            
    #     return []
