import json

clients = {}


async def notify_sala_change(sala_pk):
    group_name = str(sala_pk)
    if group_name not in clients:
        return

    payload = json.dumps({'type': 'sala_updated', 'sala_pk': sala_pk})
    dead_senders = []
    for send in list(clients[group_name]):
        try:
            await send({'type': 'websocket.send', 'text': payload})
        except Exception:
            dead_senders.append(send)

    for send in dead_senders:
        clients[group_name].discard(send)
    if group_name in clients and not clients[group_name]:
        del clients[group_name]


async def sala_application(scope, receive, send):
    path = scope.get('path', '')
    parts = path.strip('/').split('/')
    if len(parts) != 3 or parts[0] != 'ws' or parts[1] != 'salas':
        await send({'type': 'websocket.close', 'code': 1000})
        return

    sala_pk = parts[2]
    if not sala_pk.isdigit():
        await send({'type': 'websocket.close', 'code': 1000})
        return

    group_name = sala_pk
    try:
        while True:
            event = await receive()
            if event['type'] == 'websocket.connect':
                await send({'type': 'websocket.accept'})
                clients.setdefault(group_name, set()).add(send)
            elif event['type'] == 'websocket.receive':
                continue
            elif event['type'] == 'websocket.disconnect':
                break
    finally:
        if group_name in clients:
            clients[group_name].discard(send)
            if not clients[group_name]:
                del clients[group_name]
