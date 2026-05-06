import asyncio
import json
import os
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from google import genai
from google.genai import types
from scrum.agents.scrum.tools import (
    KANBAN_FUNCTION_DECLARATIONS,
    kanban_list_boards,
    kanban_get_board_detail,
    kanban_add_card,
    kanban_move_card,
    kanban_update_card,
    kanban_delete_card,
)

class ScrumLiveConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        
        # Initialize Gemini client
        api_key = os.getenv("GOOGLE_API_KEY")
        self.session_ready = asyncio.Event()
        self.client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})

        self.model_id = "gemini-3.1-flash-live-preview"
        
        # Start Gemini session
        self.session = None
        self.gemini_task = None
        
        try:
            # We use a context manager to ensure the session is handled, 
            # but since we need it to persist across receive calls, 
            # we'll manage the lifecycle manually or via a long-running task.
            self.gemini_task = asyncio.create_task(self.run_gemini_session())
        except Exception as e:
            print(f"Error starting Gemini session: {e}")
            await self.close()

    async def run_gemini_session(self):
        config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": "Puck"
                    }
                }
            },
            "tools": [{"function_declarations": KANBAN_FUNCTION_DECLARATIONS}],
            "system_instruction": (
                "You are a helpful Scrum Master assistant with access to the team's Kanban board. "
                "You can view boards, add cards, move cards between columns, update card details, and delete cards. "
                "When the user asks about tasks, first use kanban_list_boards and kanban_get_board_detail to understand the current state. "
                "When the user asks to add, move, update, or delete tasks, use the appropriate tool. "
                "Always confirm what you did after completing an action."
            )
        }


        
        try:
            async with self.client.aio.live.connect(model=self.model_id, config=config) as session:
                self.session = session
                self.session_ready.set()
                print("Gemini Live Session Started")

                
                while True:
                    async for response in session.receive():
                        if response.setup_complete:
                            print("Gemini Setup Complete")
                        
                        if response.server_content:
                            content = response.server_content
                            
                            if content.interrupted:
                                print("Gemini Interrupted")
                                await self.send(text_data=json.dumps({"type": "interrupted"}))
                            
                            if content.turn_complete:
                                print("Gemini Turn Complete")
                                await self.send(text_data=json.dumps({"type": "turn_complete"}))

                            if content.model_turn:
                                for part in content.model_turn.parts:
                                    if part.inline_data:
                                        # Forward audio data to client
                                        await self.send(text_data=json.dumps({
                                            "type": "audio",
                                            "data": base64.b64encode(part.inline_data.data).decode('utf-8')
                                        }))
                            
                            if content.input_transcription:
                                await self.send(text_data=json.dumps({
                                    "type": "transcription",
                                    "source": "user",
                                    "text": content.input_transcription.text
                                }))
                            if content.output_transcription:
                                await self.send(text_data=json.dumps({
                                    "type": "transcription",
                                    "source": "gemini",
                                    "text": content.output_transcription.text
                                }))
                        
                        if response.tool_call:
                            print(f"Tool call received: {response.tool_call}")
                            function_responses = []
                            for fc in response.tool_call.function_calls:
                                result = await self.dispatch_tool(fc.name, fc.args or {})
                                function_responses.append(types.FunctionResponse(
                                    id=fc.id,
                                    name=fc.name,
                                    response={"result": result}
                                ))
                            await session.send_tool_response(function_responses=function_responses)
                    
                    # If the loop finishes naturally, it means the turn ended.
                    # We continue the while True loop to wait for the next turn's responses.
                    print("Gemini response stream finished, waiting for next turn...")

        except Exception as e:
            import traceback
            print(f"Gemini Session Error: {e}")
            traceback.print_exc()
            await self.send(text_data=json.dumps({"type": "error", "message": str(e)}))
        finally:
            print("Gemini Session Closed")

    async def dispatch_tool(self, name: str, args: dict) -> dict:
        """Route tool calls to the appropriate kanban function."""
        TOOL_MAP = {
            "kanban_list_boards": kanban_list_boards,
            "kanban_get_board_detail": kanban_get_board_detail,
            "kanban_add_card": kanban_add_card,
            "kanban_move_card": kanban_move_card,
            "kanban_update_card": kanban_update_card,
            "kanban_delete_card": kanban_delete_card,
        }
        handler = TOOL_MAP.get(name)
        if not handler:
            return {"error": f"Unknown tool: {name}"}
        try:
            result = await handler(**args)
            # Notify frontend of changes
            if name in ("kanban_add_card", "kanban_move_card", "kanban_update_card", "kanban_delete_card"):
                await self.send(text_data=json.dumps({"type": "kanban_update"}))
            return result
        except Exception as e:
            return {"error": str(e)}


    async def disconnect(self, close_code):
        if self.gemini_task:
            self.gemini_task.cancel()
        print("ScrumLiveConsumer disconnected")

    async def receive(self, text_data=None, bytes_data=None):
        # Wait for Gemini session to be ready
        await self.session_ready.wait()
        
        if not self.session:
            return

        try:
            if text_data:
                data = json.loads(text_data)
                msg_type = data.get("type")
                
                if msg_type == "text":
                    # User sent a text message
                    text = data.get("text")
                    await self.session.send_realtime_input(text=text)
                
                elif msg_type == "audio":
                    # User sent audio chunk (Base64 encoded)
                    audio_b64 = data.get("data")
                    audio_bytes = base64.b64decode(audio_b64)
                    await self.session.send_realtime_input(audio=types.Blob(
                        data=audio_bytes,
                        mime_type="audio/pcm;rate=16000"
                    ))
        except Exception as e:
            print(f"Error sending to Gemini: {e}")
            await self.send(text_data=json.dumps({"type": "error", "message": "Gemini connection lost. Please reconnect."}))
            await self.close()


