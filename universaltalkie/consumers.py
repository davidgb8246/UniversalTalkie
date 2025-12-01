import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from urllib.parse import parse_qs

# Track connected clients
connected_clients = set()

class BaseConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # Parse the passkey from URL query string
        qs = self.scope.get("query_string", b"").decode()
        params = parse_qs(qs)
        passkey = params.get("passkey", [None])[0]

        if passkey != settings.WEBSOCKET_PASSKEY:
            # Accept first to send an error
            await self.accept()
            await self.send(json.dumps({"error": "Invalid passkey"}))
            await self.close()
            return

        # Valid passkey → accept and initialize client
        await self.accept()
        self.authenticated = True
        connected_clients.add(self.channel_name)
        await self.channel_layer.group_add("broadcast_group", self.channel_name)
        await self.send(json.dumps({"message": "Connected!", "c": len(connected_clients)}))

    async def disconnect(self, close_code):
        if getattr(self, "authenticated", False):
            connected_clients.discard(self.channel_name)
            await self.channel_layer.group_discard("broadcast_group", self.channel_name)

    async def receive(self, text_data):
        if not getattr(self, "authenticated", False):
            await self.close()
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({"error": "Invalid JSON"}))
            return

        # Info command
        if data.get("cmd") == "i":
            await self.send(json.dumps({"c": len(connected_clients)}))
            return

        # Broadcast to other clients
        await self.channel_layer.group_send(
            "broadcast_group",
            {"type": "bmsg", "sender": self.channel_name, "msg": data}
        )

    async def bmsg(self, event):
        if self.channel_name != event["sender"]:
            await self.send(json.dumps(event["msg"]))
