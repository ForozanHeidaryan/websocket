import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import ai.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HadiHesabAI.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            ai.routing.websocket_urlpatterns
        )
    ),
})

