from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.websocket.connection_manager import manager
from app.core.security import authenticate_websocket

router = APIRouter()


@router.websocket("/presence")
async def presence_socket(websocket: WebSocket):
    user = await authenticate_websocket(websocket)
    user_id = user.get("sub")
    session_id = websocket.query_params.get("session_id")

    if not session_id:
        await websocket.close(code=1008)
        return

    await manager.connect(user_id, session_id, websocket)

    try:
        while True:
            await websocket.receive_text()  # keep-alive ping
    except WebSocketDisconnect:
        await manager.disconnect(user_id, session_id)
