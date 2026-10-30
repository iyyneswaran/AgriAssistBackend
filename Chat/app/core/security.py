from jose import JWTError, jwt
from fastapi import Header, HTTPException, status, WebSocket
from app.core.config import settings


def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require_exp": True},
        )
        user_id = payload.get('id') or payload.get('sub')
        if payload.get('token_use') != 'access' or not isinstance(user_id, str) or not user_id:
            raise JWTError('Invalid access token payload')
        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def get_current_user(token: str) -> dict:
    payload = decode_jwt_token(token)

    if "id" not in payload and "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return payload


def authenticated_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Authorization header required')
    return get_current_user(authorization.split(' ', 1)[1])


def require_owner(user: dict, user_id: str) -> None:
    if (user.get('id') or user.get('sub')) != user_id:
        raise HTTPException(status_code=403, detail='Access denied')


def verify_role(user: dict, required_role: str):
    if user.get("role") != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


# -------- WebSocket Authentication -------- #

async def authenticate_websocket(websocket: WebSocket) -> dict | None:
    """Authenticate a WebSocket connection that has already been accepted.
    Returns the JWT payload dict on success, or None on failure (closes the WS).
    """
    token = websocket.query_params.get("token")

    if not token:
        await websocket.send_json({"type": "error", "detail": "Token missing"})
        await websocket.close(code=1008)
        return None

    try:
        payload = get_current_user(token)
        return payload

    except (JWTError, HTTPException):
        await websocket.send_json({"type": "error", "detail": "Invalid or expired token"})
        await websocket.close(code=1008)
        return None
