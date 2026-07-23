"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
import json

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django_asgi_app = get_asgi_application()


async def application(scope, receive, send):
    if scope['type'] == 'http':
        await django_asgi_app(scope, receive, send)
        return

    if scope['type'] == 'websocket':
        path = scope.get('path', '')
        if path.startswith('/ws/salas/'):
            from salas.consumers import sala_application
            await sala_application(scope, receive, send)
            return

    await send({'type': 'websocket.close', 'code': 1000})
