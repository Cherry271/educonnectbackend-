from typing import Dict, Set

import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


class ConnectionManager:
    def __init__(self) -> None:
        self.user_sockets: Dict[str, Set[str]] = {}
        self.online_users: Set[str] = set()

    async def connect(self, sid: str, user_id: str) -> None:
        self.user_sockets.setdefault(user_id, set()).add(sid)
        self.online_users.add(user_id)
        await sio.emit("user_online", {"user_id": user_id}, skip_sid=sid)

    async def disconnect(self, sid: str, user_id: str) -> None:
        if user_id in self.user_sockets:
            self.user_sockets[user_id].discard(sid)
            if not self.user_sockets[user_id]:
                del self.user_sockets[user_id]
                self.online_users.discard(user_id)
                await sio.emit("user_offline", {"user_id": user_id})

    async def send_to_user(self, user_id: str, event: str, data: dict) -> None:
        sids = self.user_sockets.get(user_id, set())
        for sid in sids:
            await sio.emit(event, data, to=sid)

    def is_online(self, user_id: str) -> bool:
        return user_id in self.online_users


manager = ConnectionManager()


@sio.event
async def connect(sid, environ, auth):
    user_id = (auth or {}).get("user_id") if auth else None
    if user_id:
        await manager.connect(sid, user_id)
        await sio.enter_room(sid, f"user_{user_id}")


@sio.event
async def disconnect(sid):
    for user_id, sids in list(manager.user_sockets.items()):
        if sid in sids:
            await manager.disconnect(sid, user_id)
            break


@sio.event
async def join_conversation(sid, data):
    conversation_id = data.get("conversation_id")
    if conversation_id:
        await sio.enter_room(sid, f"conv_{conversation_id}")


@sio.event
async def typing(sid, data):
    conversation_id = data.get("conversation_id")
    user_id = data.get("user_id")
    is_typing = data.get("is_typing", False)
    if conversation_id:
        await sio.emit(
            "typing",
            {"user_id": user_id, "is_typing": is_typing, "conversation_id": conversation_id},
            room=f"conv_{conversation_id}",
            skip_sid=sid,
        )


@sio.event
async def send_message(sid, data):
    conversation_id = data.get("conversation_id")
    if conversation_id:
        await sio.emit("new_message", data, room=f"conv_{conversation_id}")
