import textwrap
from typing import List, Optional

from vertexai import generative_models


def get_default_generation_config() -> generative_models.GenerationConfig:
    """Default generation config

    TODO: We should customize this based on the use case.
    """
    return generative_models.GenerationConfig(
        temperature=0.2,
        top_p=0.95,
    )


def get_default_safety_settings() -> List[generative_models.SafetySetting]:
    """Default safety settings

    TODO: We should customize this based on the use case.
    """
    return [
        generative_models.SafetySetting(
            category=generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
        generative_models.SafetySetting(
            category=generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
        generative_models.SafetySetting(
            category=generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
        generative_models.SafetySetting(
            category=generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
    ]


def create_model(
    model_name: str,
    tools: List[generative_models.Tool],
    system_instruction: str,
) -> generative_models.GenerativeModel:
    return generative_models.GenerativeModel(
        model_name=model_name,
        tools=tools,
        system_instruction=[
            system_instruction,
        ],
    )


def create_vertexai_search_tool(
    project_id: str,
    location: str,
    datastore_id: str,
) -> generative_models.Tool:
    return generative_models.Tool.from_retrieval(
        retrieval=generative_models.grounding.Retrieval(
            source=generative_models.grounding.VertexAISearch(
                project=project_id,
                location=location,
                datastore=datastore_id,
            ),
        )
    )


def get_system_instruction() -> str:
    return textwrap.dedent(
        """
        You are a helpful assistant knowledgeable about Alphabet quarterly earning reports.
        Help users with their queries related to Alphabet by only responding with information available in the Grounding Knowledge store.

        - Always refer to the tool and ground your answers in it.
        - Understand the retrieved snippet by the tool and only use that information to help users.
        - For supporting references, you can provide the Grounding tool snippets verbatim, and any other info like page number.
        - If information is not available in the tool, mention you don't have access to the information.
        - Output "answer" should be "I don't know" when the user question is irrelevant or outside the scope of the knowledge base.
        - Leave "reference_snippet" as null if you are unsure about the page and text snippet.

        The Grounding tool finds the most relevant snippets from the Alphabet earning reports data store.
        Use the information provided by the tool as your knowledge base.

        - ONLY use information available from the Grounding tool.

        - Response should ALWAYS be in the following JSON format with "answer" and "reference_snippet" as keys, e.g., {{"answer": "...", "reference_snippet": "..."}}

        ## JSON schema
        ```json
        {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "The answer to the query"
                },
                "reference_snippet": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Title of the reference snippet"
                            },
                            "raw_text": {
                                "type": "string",
                                "description": "Content of the reference raw text"
                            }
                        },
                        "required": [
                            "title",
                            "raw_text"
                        ]
                    },
                    "description": "Reference snippets used to generate the answer"
                }
            },
            "required": [
                "answer",
                "reference_snippet"
            ]
        }
        ```
        """
    )


class VertexAISearchAgent:
    def __init__(
        self,
        model: generative_models.GenerativeModel,
    ):
        # pylint: disable=line-too-long
        self.model = model

    async def asearch(
        self,
        query: str,
        generation_config: generative_models.GenerationConfig,
        safety_settings: Optional[List[generative_models.SafetySetting]],
    ) -> str:
        """Asynchronous search"""
        response = await self.model.generate_content_async(
            contents=[query],
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=True,
        )
        return response.text

    def search(
        self,
        query: str,
        generation_config: generative_models.GenerationConfig,
        safety_settings: Optional[List[generative_models.SafetySetting]],
    ) -> str:
        """Synchronous search"""
        # TODO Enable to customize generation config and safety settings
        response = self.model.generate_content(
            contents=[query],
            generation_config=generation_config,
            safety_settings=safety_settings,
            stream=False,
        )
        return response.text
