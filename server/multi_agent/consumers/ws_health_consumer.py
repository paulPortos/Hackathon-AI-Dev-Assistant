from channels.generic.websocket import JsonWebsocketConsumer


class WsHealthConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.accept()
        self.send_json({'event': 'ws_health', 'status': 'ok'})

    def receive_json(self, content, **kwargs):
        self.send_json({'event': 'echo', 'payload': content})
