import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

# Track connected clients
connected_clients = set()

class BaseConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # Accept the connection first
        await self.accept()

        # Mark client as not authenticated yet
        self.authenticated = False

    async def disconnect(self, close_code):
        if getattr(self, "authenticated", False):
            connected_clients.discard(self.channel_name)
            await self.channel_layer.group_discard("broadcast_group", self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({"error": "Invalid JSON"}))
            return

        # If not yet authenticated, expect passkey
        if not getattr(self, "authenticated", False):
            passkey = data.get("passkey")
            if passkey == settings.WEBSOCKET_PASSKEY:
                self.authenticated = True
                
                # Add to connected clients
                connected_clients.add(self.channel_name)
                await self.channel_layer.group_add("broadcast_group", self.channel_name)

                # Send welcome/info
                await self.send(json.dumps({"message": "Connected!", "c": len(connected_clients)}))
            else:
                # Wrong passkey → disconnect
                await self.send(json.dumps({"error": "Invalid passkey"}))
                await self.close()
            return

        # From here on, only authenticated clients can send messages

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
                "msg": data
            }
        )

    async def bmsg(self, event):
        if self.channel_name != event["sender"]:
            await self.send(json.dumps(event["msg"]))
