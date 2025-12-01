import json
from channels.generic.websocket import AsyncWebsocketConsumer

connected_clients = set()

class BaseConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()
        channel = self.channel_name

        connected_clients.add(channel)
        await self.channel_layer.group_add("broadcast_group", channel)

        # Send initial info
        await self.send(json.dumps({"c": len(connected_clients)}))

    async def disconnect(self, close_code):
        channel = getattr(self, "channel_name", None)
        if channel:
            connected_clients.discard(channel)
            await self.channel_layer.group_discard("broadcast_group", channel)

    async def receive(self, text_data):
        channel = self.channel_name

        # Ignore empty messages
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            # Invalid JSON, ignore instead of disconnecting
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
                "sender": channel,
                "msg": data
            }
        )

    async def bmsg(self, event):
        channel = self.channel_name
        if channel != event["sender"]:
            await self.send(json.dumps(event["msg"]))
