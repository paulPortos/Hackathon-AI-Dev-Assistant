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
    kanban_bulk_move_cards,
    GITHUB_ISSUES_FUNCTION_DECLARATIONS,
    github_list_issues,
    github_get_issue,
)
from asgiref.sync import sync_to_async
from scrum.models.scrum_session import ScrumSession
from scrum.models.scrum_message import ScrumMessage
from scrum.models.scrum_tool_call import ScrumToolCall
from projects.models.project import Project
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from urllib.parse import parse_qs
from scrum.models.github_issue import GitHubIssue

User = get_user_model()

class ScrumLiveConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Initialize attributes to avoid AttributeError in disconnect
        self.gemini_task = None
        self.session_ready = asyncio.Event()
        self.session = None
        
        # Extract project_id and optional session_id from URL
        self.project_id = self.scope['url_route']['kwargs'].get('project_id')
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        self.user = self.scope.get('user')
        
        # Buffers for aggregating streamed transcriptions
        self.user_text_buffer = ""
        self.assistant_text_buffer = ""
        
        # Fallback to JWT token in query string if user is not authenticated
        if not self.user or not self.user.is_authenticated:
            query_string = self.scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            token = query_params.get('token', [None])[0]
            if token:
                try:
                    access_token = AccessToken(token)
                    user_id = access_token['user_id']
                    self.user = await sync_to_async(User.objects.get)(id=user_id)
                    print(f"WebSocket auth success via JWT: {self.user}")
                except Exception as e:
                    print(f"WebSocket auth failed via JWT: {e}")

        if not self.user or not self.user.is_authenticated:
            print("WebSocket connect failed: User not authenticated")
            await self.close(code=4003) # Unauthorized
            return

        try:
            # Verify project exists and load/create session
            self.scrum_session = await self.get_or_create_session()
            await self.accept()
            print(f"WebSocket connected: project={self.project_id}, session={self.scrum_session.id}")
        except Exception as e:
            print(f"WebSocket connect error: {e}")
            await self.close()
            return
        
        # Initialize Gemini client
        api_key = os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})

        self.model_id = "gemini-3.1-flash-live-preview"
        
        try:
            self.gemini_task = asyncio.create_task(self.run_gemini_session())
        except Exception as e:
            print(f"Error starting Gemini session: {e}")
            await self.close()

    @sync_to_async
    def get_or_create_session(self):
        project = Project.objects.get(id=self.project_id)
        if self.session_id:
            return ScrumSession.objects.get(id=self.session_id, user=self.user, project=project)
        return ScrumSession.objects.create(user=self.user, project=project, status=ScrumSession.Status.ACTIVE)

    @sync_to_async
    def get_session_history(self):
        messages = ScrumMessage.objects.filter(session=self.scrum_session).order_by('-created_at')[:20]
        # Reverse to get chronological order
        return list(reversed(messages))

    @sync_to_async
    def save_message(self, role, text, input_type='text'):
        return ScrumMessage.objects.create(
            session=self.scrum_session,
            role=role,
            text_content=text,
            input_type=input_type
        )

    @sync_to_async
    def save_tool_call(self, name, args, result, status):
        return ScrumToolCall.objects.create(
            session=self.scrum_session,
            tool_name=name,
            safe_input_summary=args,
            safe_result_summary=result,
            status=status
        )

    def format_issues_for_prompt(self, issues):
        """Format issues list into a concise string for system prompt."""
        if not issues:
            return "No open GitHub issues found."
        
        lines = []
        for i in issues:
            lines.append(f"#{i.github_number}: {i.title}")
        return "\n".join(lines)

    async def run_gemini_session(self):
        # Fetch history to provide context
        history = await self.get_session_history()
        history_text = "\n".join([f"{m.role.upper()}: {m.text_content}" for m in history])
        
        base_instruction = (
            "You are a helpful Scrum Master assistant with access to the team's Kanban board. "
            "You can view boards, add cards, move cards between columns, update card details, and delete cards. "
            "When the user asks about tasks, first use kanban_list_boards and kanban_get_board_detail to understand the current state. "
            "When the user asks to add, move, or update tasks, use the appropriate tool. "
            "When the user asks to move multiple tasks, ALWAYS use kanban_bulk_move_cards instead of moving them one by one. "
            "CRITICAL SAFEGUARD FOR DELETION: When the user asks to delete a card, NEVER use the kanban_delete_card tool immediately. First, verbally ask the user for confirmation (e.g., 'Are you sure you want to delete this task?'). Only proceed to use the kanban_delete_card tool if the user explicitly confirms."
            "Always confirm what you did after completing an action."
        )

        if history_text:
            system_instruction = f"{base_instruction}\n\nPrevious conversation context:\n{history_text}\n\nPlease continue the conversation naturally based on this context."
        else:
            system_instruction = base_instruction

        project = await sync_to_async(Project.objects.get)(id=self.project_id)
        
        system_instruction += f"\n\n## Project GitHub Repository: {project.github_full_name}"
        system_instruction += "\n\nYou can use the github_* tools to query live data for issues."

        config = {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": "Puck"
                    }
                }
            },
            "tools": [{"function_declarations": KANBAN_FUNCTION_DECLARATIONS + GITHUB_ISSUES_FUNCTION_DECLARATIONS}],
            "system_instruction": system_instruction
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
                                await self.flush_buffers()
                                await self.send(text_data=json.dumps({"type": "interrupted"}))
                            
                            if content.turn_complete:
                                print("Gemini Turn Complete")
                                await self.flush_buffers()
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
                                text = content.input_transcription.text
                                self.user_text_buffer += text
                                await self.send(text_data=json.dumps({
                                    "type": "transcription",
                                    "source": "user",
                                    "text": text
                                }))
                            if content.output_transcription:
                                text = content.output_transcription.text
                                self.assistant_text_buffer += text
                                await self.send(text_data=json.dumps({
                                    "type": "transcription",
                                    "source": "gemini",
                                    "text": text
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
            "kanban_bulk_move_cards": kanban_bulk_move_cards,
            "github_list_issues": github_list_issues,
            "github_get_issue": github_get_issue,
        }
        handler = TOOL_MAP.get(name)
        if not handler:
            return {"error": f"Unknown tool: {name}"}
        try:
            # Special handling for tools that need 'user' or 'project_id' context
            if name in ("github_list_issues", "github_get_issue"):
                result = await handler(project_id=self.project_id, user=self.user, **args)
            else:
                result = await handler(**args)
            
            await self.save_tool_call(name, args, result, ScrumToolCall.Status.SUCCESS)
            
            # Notify frontend of changes
            if name in ("kanban_add_card", "kanban_move_card", "kanban_update_card", "kanban_delete_card", "kanban_bulk_move_cards"):
                await self.send(text_data=json.dumps({"type": "kanban_update"}))
                
            return result
        except Exception as e:
            await self.save_tool_call(name, args, {"error": str(e)}, ScrumToolCall.Status.ERROR)
            return {"error": str(e)}

    async def flush_buffers(self):
        """Save buffered transcriptions to the database and clear them."""
        if self.user_text_buffer.strip():
            await self.save_message(ScrumMessage.Role.USER, self.user_text_buffer.strip(), ScrumMessage.InputType.AUDIO)
            self.user_text_buffer = ""
        
        if self.assistant_text_buffer.strip():
            await self.save_message(ScrumMessage.Role.ASSISTANT, self.assistant_text_buffer.strip(), ScrumMessage.InputType.AUDIO)
            self.assistant_text_buffer = ""


    async def disconnect(self, close_code):
        if getattr(self, 'gemini_task', None):
            self.gemini_task.cancel()
        print(f"ScrumLiveConsumer disconnected (code={close_code})")

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
                    await self.save_message(ScrumMessage.Role.USER, text, ScrumMessage.InputType.TEXT)
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

class KanbanConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.board_id = self.scope['url_route']['kwargs'].get('board_id')
        self.group_name = f"kanban_board_{self.board_id}"

        # Join board group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        print(f"KanbanConsumer connected to {self.group_name}")

    async def disconnect(self, close_code):
        # Leave board group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        print(f"KanbanConsumer disconnected")

    async def kanban_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))


