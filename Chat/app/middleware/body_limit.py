"""Bound HTTP request bodies, including chunked multipart uploads."""
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


class BodySizeLimit:
    def __init__(self, app, max_bytes=12 * 1024 * 1024):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        for key, value in scope.get('headers', []):
            if key.lower() == b'content-length':
                try:
                    size = int(value)
                    if size < 0:
                        raise ValueError()
                except ValueError:
                    return await JSONResponse({'detail': 'Invalid content length'}, status_code=400)(scope, receive, send)
                if size > self.max_bytes:
                    return await JSONResponse({'detail': 'Request body too large'}, status_code=413)(scope, receive, send)
        total = 0

        async def bounded_receive():
            nonlocal total
            message = await receive()
            if message['type'] == 'http.request':
                total += len(message.get('body', b''))
                if total > self.max_bytes:
                    raise HTTPException(status_code=413, detail='Request body too large')
            return message

        await self.app(scope, bounded_receive, send)
