import asyncio
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from channels.db import database_sync_to_async

from multi_agent.agents.sr_dev.workflows import senior_dev_message_process
from multi_agent.models import SeniorDevFinding, SeniorDevMessage
from multi_agent.selectors import senior_dev_message_list, senior_dev_session_get_for_user
from multi_agent.serializers import SeniorDevFindingSerializer, SeniorDevMessageSerializer


class SeniorDevSessionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        print(f"[WS] Connect request for {self.scope.get('path')}")
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            print("[WS] Auth failed")
            await self.accept()
            error_detail = self.scope.get('jwt_error') or 'Unauthorized'
            await self.send_json({'event': 'error', 'message': error_detail})
            await self.close(code=4401)
            return

        session_id = self.scope.get('url_route', {}).get('kwargs', {}).get('session_id')
        print(f"[WS] Session ID: {session_id}")
        try:
            session_id = int(session_id)
        except (TypeError, ValueError):
            print(f"[WS] Invalid session ID type: {type(session_id)}")
            await self.close(code=4400)
            return

        try:
            print(f"[WS] Looking up session {session_id} for user {user}")
            self.session = await database_sync_to_async(senior_dev_session_get_for_user)(
                session_id=session_id, user=user
            )
            print(f"[WS] Session found: {self.session}")
        except ObjectDoesNotExist:
            print(f"[WS] Session {session_id} not found for user {user}")
            await self.close(code=4404)
            return
        except Exception as e:
            print(f"[WS] Error during session lookup: {e}")
            await self.close(code=4500)
            return

        await self.accept()
        print("[WS] Connection accepted")
        await self._send_history()

    async def receive_json(self, content, **kwargs):
        action = (content or {}).get('action')
        if action != 'send_message':
            await self._send_error('Unsupported action')
            return

        input_type = str(content.get('input_type') or SeniorDevMessage.InputType.OPEN_TEXT).strip()
        if input_type == SeniorDevMessage.InputType.TEXT:
            input_type = SeniorDevMessage.InputType.OPEN_TEXT

        allowed_types = {
            SeniorDevMessage.InputType.OPEN_TEXT,
            SeniorDevMessage.InputType.CHOICE,
        }
        if input_type not in allowed_types:
            await self._send_error('Unsupported input_type')
            return

        text = str(content.get('text') or '')
        choice = str(content.get('choice') or '')
        choice_payload = content.get('choice_payload')
        if choice_payload is not None and not isinstance(choice_payload, dict):
            choice_payload = {}

        loop = asyncio.get_running_loop()

        def emit_tool_event_sync(event):
            asyncio.run_coroutine_threadsafe(self.send_json(event), loop)

        try:
            # Run the blocking agent process in a thread executor
            payload = await loop.run_in_executor(
                None,
                lambda: senior_dev_message_process(
                    session=self.session,
                    user=self.scope['user'],
                    input_type=input_type,
                    text=text,
                    choice=choice,
                    choice_payload=choice_payload,
                    emit_tool_event=emit_tool_event_sync,
                )
            )
        except ValueError as exc:
            await self._send_error(str(exc))
            return
        except Exception as e:
            print(f"Error in senior_dev_message_process: {e}")
            await self._send_error('Failed to process message')
            return

        await self._send_message_by_id(payload.get('user_message_id'))
        await self._send_message_by_id(payload.get('assistant_message_id'))
        await self._send_findings_by_ids(payload.get('finding_ids'))

    async def _send_history(self):
        @database_sync_to_async
        def get_serialized_history():
            messages = senior_dev_message_list(self.session)
            return SeniorDevMessageSerializer(messages, many=True).data

        serialized = await get_serialized_history()
        await self.send_json({'event': 'history', 'messages': serialized})

    async def _send_message_by_id(self, message_id):
        if not message_id:
            return

        @database_sync_to_async
        def get_serialized_message():
            try:
                message = SeniorDevMessage.objects.get(id=message_id)
                return SeniorDevMessageSerializer(message).data
            except SeniorDevMessage.DoesNotExist:
                return None

        serialized = await get_serialized_message()
        if serialized:
            await self.send_json({'event': 'message', 'message': serialized})

    async def _send_findings_by_ids(self, finding_ids):
        if not finding_ids:
            return
        if not isinstance(finding_ids, (list, tuple)):
            return

        @database_sync_to_async
        def get_serialized_findings():
            findings = SeniorDevFinding.objects.filter(id__in=finding_ids)
            if not findings:
                return []
            return SeniorDevFindingSerializer(findings, many=True).data

        serialized = await get_serialized_findings()
        if serialized:
            await self.send_json({'event': 'findings', 'findings': serialized})

    async def _send_error(self, message):
        await self.send_json({'event': 'error', 'message': str(message)})

