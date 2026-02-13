from jose import JWTError, jwt
from fastapi import HTTPException, status, WebSocket
from app.core.config import settings


def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def get_current_user(token: str) -> dict:
    payload = decode_jwt_token(token)

    if "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return payload


def verify_role(user: dict, required_role: str):
    if user.get("role") != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


# -------- WebSocket Authentication -------- #

async def authenticate_websocket(websocket: WebSocket) -> dict:
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        raise Exception("Token missing")

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload

    except JWTError:
        await websocket.close(code=1008)
        raise Exception("Invalid token")
