import base64
import binascii

from channels.generic.websocket import JsonWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import SimpleUploadedFile

from multi_agent.agents.sr_dev.workflows import senior_dev_message_process
from multi_agent.models import SeniorDevMessage
from multi_agent.selectors import senior_dev_message_list, senior_dev_session_get_for_user
from multi_agent.serializers import SeniorDevMessageSerializer


class SeniorDevSessionConsumer(JsonWebsocketConsumer):
    def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            self.close(code=4401)
            return

        session_id = self.scope.get('url_route', {}).get('kwargs', {}).get('session_id')
        try:
            session_id = int(session_id)
        except (TypeError, ValueError):
            self.close(code=4400)
            return

        try:
            self.session = senior_dev_session_get_for_user(session_id=session_id, user=user)
        except ObjectDoesNotExist:
            self.close(code=4404)
            return

        self.accept()
        self._send_history()

    def receive_json(self, content, **kwargs):
        action = (content or {}).get('action')
        if action != 'send_message':
            self._send_error('Unsupported action')
            return

        input_type = str(content.get('input_type') or SeniorDevMessage.InputType.OPEN_TEXT).strip()
        if input_type == SeniorDevMessage.InputType.TEXT:
            input_type = SeniorDevMessage.InputType.OPEN_TEXT

        allowed_types = {
            SeniorDevMessage.InputType.OPEN_TEXT,
            SeniorDevMessage.InputType.CHOICE,
            SeniorDevMessage.InputType.AUDIO,
        }
        if input_type not in allowed_types:
            self._send_error('Unsupported input_type')
            return

        text = str(content.get('text') or '')
        choice = str(content.get('choice') or '')
        choice_payload = content.get('choice_payload')
        if choice_payload is not None and not isinstance(choice_payload, dict):
            choice_payload = {}
        audio_payload = content.get('audio')
        audio_file = None

        if input_type == SeniorDevMessage.InputType.AUDIO:
            try:
                audio_file = self._build_audio_file(audio_payload)
            except ValueError as exc:
                self._send_error(str(exc))
                return

        try:
            payload = senior_dev_message_process(
                session=self.session,
                user=self.scope['user'],
                input_type=input_type,
                text=text,
                choice=choice,
                choice_payload=choice_payload,
                audio_file=audio_file,
            )
        except ValueError as exc:
            self._send_error(str(exc))
            return
        except Exception:
            self._send_error('Failed to process message')
            return

        self._send_message_by_id(payload.get('user_message_id'))
        self._send_message_by_id(payload.get('assistant_message_id'))

    def _send_history(self):
        messages = senior_dev_message_list(self.session)
        serialized = SeniorDevMessageSerializer(messages, many=True).data
        self.send_json({'event': 'history', 'messages': serialized})

    def _send_message_by_id(self, message_id):
        if not message_id:
            return
        try:
            message = SeniorDevMessage.objects.get(id=message_id)
        except SeniorDevMessage.DoesNotExist:
            return
        serialized = SeniorDevMessageSerializer(message).data
        self.send_json({'event': 'message', 'message': serialized})

    def _build_audio_file(self, audio_payload):
        if not isinstance(audio_payload, dict):
            raise ValueError('audio payload is required')

        base64_data = str(audio_payload.get('base64') or '').strip()
        if base64_data.startswith('data:'):
            base64_data = base64_data.split(',', 1)[1] if ',' in base64_data else ''

        if not base64_data:
            raise ValueError('audio payload is missing data')

        try:
            audio_bytes = base64.b64decode(base64_data)
        except (binascii.Error, ValueError) as exc:
            raise ValueError('audio payload is invalid') from exc

        if not audio_bytes:
            raise ValueError('audio payload is empty')

        file_name = str(audio_payload.get('file_name') or 'audio')
        content_type = str(audio_payload.get('content_type') or 'application/octet-stream')
        return SimpleUploadedFile(file_name, audio_bytes, content_type=content_type)

    def _send_error(self, message):
        self.send_json({'event': 'error', 'message': str(message)})
