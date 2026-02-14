from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from app.core.config import settings


class JWTMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
            )

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            request.state.user = payload

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return await call_next(request)
