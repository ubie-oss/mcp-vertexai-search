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

import asyncio
import os
import sys
import traceback

import pyaudio
import streamlit as st
from google import genai

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
CONFIG = {"generation_config": {"response_modalities": ["TEXT"]}}

pya = pyaudio.PyAudio()


class AudioLoop:
    def __init__(self):
        self.out_queue = None
        self.session = None
        self.audio_stream = None  # Initialize audio_stream to None
        self.receive_text_task = None
        self.send_realtime_task = None

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
            if text := response.text:
                full_text += text
                message_placeholder.markdown(full_text + "▌")  # Add a cursor effect
        message_placeholder.markdown(full_text)  # Final response without cursor

    async def run(self, message_placeholder):
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
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
    st.title("Voice Chat with Gemini")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.button("Start Voice Chat"):
        audio_loop = AudioLoop()
        message_placeholder = st.empty()  # Placeholder for streaming response
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
                await audio_loop.run(
                    assistant_msg_placeholder
                )  # Pass placeholder to run
                user_msg_placeholder.markdown(
                    "You: (voice input)"
                )  # Indicate voice input finished
                current_assistant_message["content"] = (
                    assistant_msg_placeholder._arrow_delta_text_proto.delta.markdown
                )  # Capture final response

            asyncio.run(process_audio())
