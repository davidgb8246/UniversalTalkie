import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.urls import path
from universaltalkie.consumers import BaseConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'universaltalkie.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/", BaseConsumer.as_asgi()),
        ])
    ),
})
