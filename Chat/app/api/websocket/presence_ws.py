from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.websocket.connection_manager import manager
from app.core.security import authenticate_websocket
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/presence")
async def presence_socket(websocket: WebSocket):
    user_id = None
    session_id = None

    try:
        # Must accept the connection FIRST, then authenticate
        await websocket.accept()

        user = await authenticate_websocket(websocket)
        if user is None:
            return

        user_id = user.get("id") or user.get("sub")
        session_id = websocket.query_params.get("session_id")

        if not session_id:
            await websocket.send_json({"type": "error", "detail": "session_id is required"})
            await websocket.close(code=1008)
            return

        await manager.connect(user_id, session_id, websocket)
        logger.info(f"[WS] Presence connected: user={user_id}, session={session_id}")

        try:
            while True:
                await websocket.receive_text()  # keep-alive ping
        except WebSocketDisconnect:
            logger.info(f"[WS] Presence disconnected: session={session_id}")

    except WebSocketDisconnect:
        logger.info(f"[WS] Presence disconnected during setup: session={session_id}")
    except Exception as e:
        logger.error(f"[WS] Presence error: {e}")
    finally:
        if user_id and session_id:
            await manager.disconnect(user_id, session_id)
