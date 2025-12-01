import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from django.conf import settings
from urllib.parse import parse_qs

# Track connected clients
connected_clients = set()

class BaseConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # Subprotocols sent by browser
        # Sec-WebSocket-Protocol
        # 
        # const ws = new WebSocket(
        #     `ws://HOST:PORT/ws/`,
        #     WEBSOCKET_PASSKEY
        # );

        subprotocols = self.scope.get("subprotocols", [])
        valid_key = settings.WEBSOCKET_PASSKEY

        # If key missing or wrong → Reject handshake
        if valid_key not in subprotocols:
            raise DenyConnection("Invalid passkey")

        # Accept WebSocket with same selected subprotocol
        await self.accept(subprotocol=valid_key)

        # Track client
        connected_clients.add(self.channel_name)
        await self.channel_layer.group_add("broadcast_group", self.channel_name)

        # Send initial info
        await self.send(json.dumps({
            "c": len(connected_clients)
        }))

    async def disconnect(self, close_code):
        connected_clients.discard(self.channel_name)
        await self.channel_layer.group_discard("broadcast_group", self.channel_name)

    async def receive(self, text_data):
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
            {
                "type": "bmsg",
                "sender": self.channel_name,
                "msg": data,
            }
        )

    async def bmsg(self, event):
        if self.channel_name != event["sender"]:
            await self.send(json.dumps(event["msg"]))
