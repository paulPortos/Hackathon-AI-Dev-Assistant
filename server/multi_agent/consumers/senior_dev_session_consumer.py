from channels.generic.websocket import JsonWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist

from multi_agent.agents.sr_dev.workflows import senior_dev_message_process
from multi_agent.models import SeniorDevFinding, SeniorDevMessage
from multi_agent.selectors import senior_dev_message_list, senior_dev_session_get_for_user
from multi_agent.serializers import SeniorDevFindingSerializer, SeniorDevMessageSerializer


class SeniorDevSessionConsumer(JsonWebsocketConsumer):
    def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            self.accept()
            error_detail = self.scope.get('jwt_error') or 'Unauthorized'
            self.send_json({'event': 'error', 'message': error_detail})
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
        }
        if input_type not in allowed_types:
            self._send_error('Unsupported input_type')
            return

        text = str(content.get('text') or '')
        choice = str(content.get('choice') or '')
        choice_payload = content.get('choice_payload')
        if choice_payload is not None and not isinstance(choice_payload, dict):
            choice_payload = {}

        try:
            payload = senior_dev_message_process(
                session=self.session,
                user=self.scope['user'],
                input_type=input_type,
                text=text,
                choice=choice,
                choice_payload=choice_payload,
            )
        except ValueError as exc:
            self._send_error(str(exc))
            return
        except Exception:
            self._send_error('Failed to process message')
            return

        self._send_message_by_id(payload.get('user_message_id'))
        self._send_message_by_id(payload.get('assistant_message_id'))
        self._send_findings_by_ids(payload.get('finding_ids'))

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

    def _send_findings_by_ids(self, finding_ids):
        if not finding_ids:
            return
        if not isinstance(finding_ids, (list, tuple)):
            return
        findings = SeniorDevFinding.objects.filter(id__in=finding_ids)
        if not findings:
            return
        serialized = SeniorDevFindingSerializer(findings, many=True).data
        self.send_json({'event': 'findings', 'findings': serialized})

    def _send_error(self, message):
        self.send_json({'event': 'error', 'message': str(message)})
