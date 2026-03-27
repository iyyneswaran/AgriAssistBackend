from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.websocket.connection_manager import manager
from app.core.security import authenticate_websocket
from app.services.chat.chat_service import generate_ai_response
from app.services.chat.streaming_service import stream_tokens
from app.db.session import AsyncSessionLocal
from app.db.repositories.message_repo import MessageRepository
from app.db.models.message import MessageSender
import uuid
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/chat")
async def chat_socket(websocket: WebSocket):
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
        logger.info(f"[WS] Connected: user={user_id}, session={session_id}")

        while True:
            try:
                data = await websocket.receive_json()

                if data.get("type") == "chat_message":
                    language = data.get("language", "en")
                    content = data.get("content", "")
                    latitude = data.get("latitude")
                    longitude = data.get("longitude")

                    if not content.strip():
                        await manager.send_personal_message(
                            session_id,
                            {"type": "error", "detail": "Empty message"}
                        )
                        continue

                    # Save USER message to database
                    try:
                        async with AsyncSessionLocal() as db:
                            await MessageRepository.create(
                                db=db,
                                message_id=str(uuid.uuid4()),
                                conversation_id=session_id,
                                sender=MessageSender.USER,
                                content=content
                            )
                    except Exception as db_err:
                        logger.warning(f"[WS] Failed to save user message to DB: {db_err}")
                        # Continue anyway — don't block chat for DB errors

                    # Generate AI response
                    try:
                        response_text = await generate_ai_response(
                            user_id=user_id,
                            session_id=session_id,
                            language=language,
                            content=content,
                            latitude=latitude,
                            longitude=longitude,
                        )
                    except Exception as ai_err:
                        logger.error(f"[WS] AI generation error: {ai_err}")
                        response_text = "Sorry, I couldn't process your request right now. Please try again."

                    # Stream tokens to client
                    async for token in stream_tokens(response_text):
                        await manager.send_personal_message(
                            session_id,
                            {"type": "ai_token", "content": token},
                        )

                    await manager.send_personal_message(
                        session_id,
                        {"type": "ai_complete"},
                    )

                    # Save AI response to database
                    try:
                        async with AsyncSessionLocal() as db:
                            await MessageRepository.create(
                                db=db,
                                message_id=str(uuid.uuid4()),
                                conversation_id=session_id,
                                sender=MessageSender.AI,
                                content=response_text
                            )
                    except Exception as db_err:
                        logger.warning(f"[WS] Failed to save AI message to DB: {db_err}")

            except WebSocketDisconnect:
                logger.info(f"[WS] Client disconnected: session={session_id}")
                break
            except Exception as e:
                logger.error(f"[WS] Message processing error: {traceback.format_exc()}")
                try:
                    await manager.send_personal_message(
                        session_id,
                        {"type": "error", "detail": f"Processing failed: {str(e)}"}
                    )
                except:
                    break

    except WebSocketDisconnect:
        logger.info(f"[WS] Disconnected during setup: session={session_id}")
    except Exception as e:
        logger.error(f"[WS] Top-level error: {traceback.format_exc()}")
        try:
            await websocket.send_json({"type": "error", "detail": str(e)})
            await websocket.close(code=1011)
        except:
            pass
    finally:
        if user_id and session_id:
            await manager.disconnect(user_id, session_id)
            logger.info(f"[WS] Cleaned up: user={user_id}, session={session_id}")
