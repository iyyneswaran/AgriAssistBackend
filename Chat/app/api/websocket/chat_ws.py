from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.websocket.connection_manager import manager
from app.core.security import authenticate_websocket
from app.services.chat.chat_service import generate_ai_response
from app.services.chat.streaming_service import stream_tokens

router = APIRouter()


@router.websocket("/chat")
async def chat_socket(websocket: WebSocket):
    # Must accept the connection FIRST, then authenticate
    await websocket.accept()

    user = await authenticate_websocket(websocket)
    if user is None:
        return

    user_id = user.get("sub")
    session_id = websocket.query_params.get("session_id")

    if not session_id:
        await websocket.send_json({"type": "error", "detail": "session_id is required"})
        await websocket.close(code=1008)
        return

    await manager.connect(user_id, session_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "chat_message":
                language = data.get("language")
                content = data.get("content")

                response_text = await generate_ai_response(
                    user_id=user_id,
                    session_id=session_id,
                    language=language,
                    content=content,
                )

                async for token in stream_tokens(response_text):
                    await manager.send_personal_message(
                        session_id,
                        {
                            "type": "ai_token",
                            "content": token,
                        },
                    )

                await manager.send_personal_message(
                    session_id,
                    {
                        "type": "ai_complete"
                    },
                )

    except WebSocketDisconnect:
        await manager.disconnect(user_id, session_id)

