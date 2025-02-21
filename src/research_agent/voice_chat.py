# -*- coding: utf-8 -*-
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import asyncio
import os
import sys
import textwrap
import traceback
from typing import Optional

import pyaudio
import streamlit as st
from google import genai
from google.genai import types
from google.genai.live import AsyncSession
from loguru import logger

from research_agent.mcp_client import MCPClient
from research_agent.utils import to_gemini_function_declarations

if sys.version_info < (3, 11, 0):
    import exceptiongroup
    import taskgroup

    asyncio.TaskGroup = taskgroup.TaskGroup
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "models/gemini-2.0-flash-exp"

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"), http_options={"api_version": "v1alpha"}
)

# While Gemini 2.0 Flash is in experimental preview mode, only one of AUDIO or
# TEXT may be passed here.
# CONFIG = {"generation_config": {"response_modalities": ["TEXT"]}}

pya = pyaudio.PyAudio()


class AudioLoop:
    def __init__(self, mcp_server_url: Optional[str] = None):
        self.out_queue = None
        self.session: AsyncSession = None
        self.audio_stream = None  # Initialize audio_stream to None
        self.receive_text_task = None
        self.send_realtime_task = None
        self.mcp_server_url = mcp_server_url
        self.mcp_client: Optional[MCPClient] = None
        self.config = None

    async def get_config(self):
        """Get the config for the session"""
        if self.config is None:
            # Connect to MCP server
            if self.mcp_server_url is not None:
                self.mcp_client = MCPClient(name="document_search")
                await self.mcp_client.connect_to_server(self.mcp_server_url)

            function_declarations = []
            if self.mcp_client is not None:
                logger.debug("Getting MCP tools")
                mcp_response = await self.mcp_client.list_tools()
                logger.debug(f"MCP tools: {mcp_response}")
                function_declarations = [
                    # to_gemini_function_declarations(t).model_dump(
                    #     exclude_none=True, exclude_unset=True
                    # )
                    to_gemini_function_declarations(t)
                    for t in mcp_response.tools
                ]
            self.config = {
                "generation_config": {
                    "response_modalities": ["TEXT"],
                    # "tools": genai_tools,
                },
                "tools": [
                    {"function_declarations": function_declarations},
                    # {"code_execution": None},
                ],
                "system_instruction": textwrap.dedent("""\
                    You are a helpful assistant that can answer questions by searching the documents.
                    You have to use the tools provided to you to answer the questions.
                    You can't use the code execution feature.
                    """),
            }
            logger.debug(f"Config: {self.config}")
            # if mcp_client:
            #     await mcp_client.cleanup()
        return self.config

    async def send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send(input=msg)

    async def listen_audio(self):
        mic_info = pya.get_default_input_device_info()
        self.audio_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        if __debug__:
            kwargs = {"exception_on_overflow": False}
        else:
            kwargs = {}
        while True:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})

    async def receive_text(self, message_placeholder):
        """Background task to reads from the websocket and print text chunks"""
        full_text = ""
        turn = self.session.receive()
        async for response in turn:
            logger.debug(f"Response: {response}")
            if response.tool_call:
                try:
                    await self.handle_tool_call(self.session, response.tool_call)
                except Exception as e:
                    logger.error(f"Error handling tool call: {e}")
            if text := response.text:
                full_text += text
                message_placeholder.markdown(full_text + "▌")  # Add a cursor effect
        message_placeholder.markdown(full_text)  # Final response without cursor

    async def handle_tool_call(self, session, tool_call: types.LiveServerToolCall):
        """Handle tool calls from the assistant"""
        # mcp_client = MCPClient(name="document-search")
        # await mcp_client.connect_to_server(self.mcp_server_url)

        for fc in tool_call.function_calls:
            logger.debug(f"Tool call: {fc}")
            tool_response = types.LiveClientToolResponse(
                function_responses=[
                    types.FunctionResponse(
                        name=fc.name,
                        id=fc.id,
                        response={
                            "result": await self.mcp_client.call_tool(fc.name, fc.args)
                        },
                    )
                ]
            )
        # await mcp_client.cleanup()
        await session.send(input=tool_response)

    async def run(self, message_placeholder):
        try:
            config = await self.get_config()
            logger.debug(f"Config: {config}")
            async with (
                client.aio.live.connect(model=MODEL, config=config) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.out_queue = asyncio.Queue(maxsize=5)

                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                tg.create_task(
                    self.receive_text(message_placeholder)
                )  # Pass placeholder

        except asyncio.CancelledError:
            pass
        except ExceptionGroup as EG:
            if self.audio_stream:  # Check if audio_stream is initialized before closing
                self.audio_stream.close()
            traceback.print_exception(EG)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mcp-server-url", type=str, default=None, required=False)
    parsed_args = parser.parse_args()
    mcp_server_url = parsed_args.mcp_server_url

    st.title("Voice Chat with Gemini")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    voice_chat_on = st.checkbox("Voice Chat")

    if voice_chat_on:
        audio_loop = AudioLoop(mcp_server_url=mcp_server_url)
        st.empty()  # Placeholder for streaming response
        with st.chat_message("user"):
            st.markdown("Listening...")
            user_msg_placeholder = st.empty()

        with st.chat_message("assistant"):
            assistant_msg_placeholder = st.empty()
            st.session_state.messages.append(
                {"role": "assistant", "content": ""}
            )  # Initialize assistant message in history
            current_assistant_message = st.session_state.messages[-1]

            async def process_audio():
                while voice_chat_on:
                    await audio_loop.run(
                        assistant_msg_placeholder
                    )  # Pass placeholder to run
                    user_msg_placeholder.markdown(
                        "You: (voice input)"
                    )  # Indicate voice input finished
                    current_assistant_message["content"] = (
                        assistant_msg_placeholder.markdown
                    )  # Capture final response
                    # break # remove after implementing stop mechanism

            asyncio.run(process_audio())
