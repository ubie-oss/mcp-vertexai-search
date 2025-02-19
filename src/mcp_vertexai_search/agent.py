import textwrap
from typing import List, Optional

from vertexai import generative_models

from mcp_vertexai_search.config import DataStoreConfig

# class Reference(BaseModel):
#     """Reference"""

#     title: str = Field(..., description="Title of the reference snippet")
#     raw_text: str = Field(..., description="Content of the reference raw text")


# class SearchResponse(BaseModel):
#     """Search response"""

#     answer: str = Field(..., description="The answer to the query")
#     references: List[Reference] = Field(
#         ..., description="References used to generate the answer"
#     )


def get_generation_config(
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
) -> generative_models.GenerationConfig:
    """Default generation config

    TODO: We should customize this based on the use case.
    """
    return generative_models.GenerationConfig(
        temperature=temperature,
        top_p=top_p,
        response_mime_type="application/json",
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
    """Create a Vertex AI search tool"""
    return generative_models.Tool.from_retrieval(
        retrieval=generative_models.grounding.Retrieval(
            source=generative_models.grounding.VertexAISearch(
                project=project_id,
                location=location,
                datastore=datastore_id,
            ),
        )
    )


def create_vertex_ai_tools(
    data_stores: List[DataStoreConfig],
) -> List[generative_models.Tool]:
    """Create a list of Vertex AI search tools"""
    return [
        create_vertexai_search_tool(
            data_store.project_id, data_store.location, data_store.datastore_id
        )
        for data_store in data_stores
    ]


def get_system_instruction() -> str:
    return textwrap.dedent(
        """
        You are a helpful assistant knowledgeable about Alphabet quarterly earning reports.
        Help users with their queries related to Alphabet by only responding with information available in the Grounding Knowledge store.

        - Always refer to the tool and ground your answers in it.
        - Understand the retrieved snippet by the tool and only use that information to help users.
        - For supporting references, you can provide the Grounding tool snippets verbatim, and any other info like page number.
        - If information is not available in the tool, mention you don't have access to the information and do not try to make up an answer.
        - Output "answer" should be "I don't know" when the user question is irrelevant or outside the scope of the knowledge base.
        - Leave "references" as an empty list if you are unsure about the page and text snippet or if no relevant snippet is found.

        The Grounding tool finds the most relevant snippets from the Alphabet earning reports data store.
        Use the information provided by the tool as your knowledge base.

        - ONLY use information available from the Grounding tool.
        - DO NOT make up information or invent details not present in the retrieved snippets.

        Response should ALWAYS be in the following JSON format:
        ## JSON schema
        {
            "answer": {
                "type": "string",
                "description": "The answer to the user's query"
            },
            "references": [
                {
                    "title": {
                        "type": "string",
                        "description": "The title of the reference"
                    },
                    "raw_text": {
                        "type": "string",
                        "description": "The raw text in the reference"
                    }
                }
            ]
        }
        """
    ).strip()


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
