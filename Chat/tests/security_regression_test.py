"""Offline security checks: no real secrets, service startup or provider calls."""
import asyncio
import io
import os
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock
import pytest

# Never load the checkout's .env during regression tests.
_cwd = os.getcwd()
with tempfile.TemporaryDirectory() as directory:
    os.chdir(directory)
    with patch.dict(os.environ, {'JWT_SECRET': 'offline-security-test-secret',
            'DATABASE_URL': 'postgresql://test:test@localhost/test', 'GEMINI_API_KEY': 'test'}, clear=True):
        from app.core.config import settings
    os.chdir(_cwd)

from jose import jwt
from fastapi import FastAPI, Depends, HTTPException, UploadFile
from fastapi.testclient import TestClient
from app.core.security import authenticated_user, get_current_user, require_owner
from app.core.push_security import validate_push_endpoint, PushSession
from app.api.http import voice, admin, sensor, scan
from app.api.websocket import chat_ws
from app.api.websocket.connection_manager import ConnectionManager
from app.services.voice import audio_processor
from app.middleware import rate_limiter
from app.core.rate_limiter import _request_log


def token(**claims):
    return jwt.encode({'id': 'alice', 'token_use': 'access', 'role': 'FARMER',
        'exp': int(time.time()) + 300, **claims}, settings.JWT_SECRET, algorithm='HS256')


def headers(**claims):
    return {'Authorization': 'Bearer ' + token(**claims)}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    import socket
    original_connect = socket.socket.connect
    def blocked(sock, address):
        # Windows asyncio implements its wakeup socketpair over loopback.
        if isinstance(address, tuple) and address[0] in ('127.0.0.1', '::1'):
            return original_connect(sock, address)
        raise AssertionError('External network is forbidden in security tests')
    monkeypatch.setattr(socket.socket, 'connect', blocked)
    _request_log.clear()


@pytest.mark.parametrize('claims', [{'token_use': 'refresh'}, {'token_use': None}, {'id': ''}, {'id': []}, {'exp': 1}])
def test_bad_access_tokens(claims):
    with pytest.raises(HTTPException): get_current_user(token(**claims))


def test_valid_access_and_owner():
    assert get_current_user(token())['id'] == 'alice'
    require_owner({'id': 'alice'}, 'alice')
    with pytest.raises(HTTPException): require_owner({'id': 'mallory'}, 'alice')


@pytest.mark.parametrize('endpoint', ['https://127.0.0.1/private', 'https://[::1]/',
    'https://169.254.169.254/', 'https://fcm.googleapis.com.evil.test/',
    'https://fcm.googleapis.com@evil.test/', 'https://evil.test@fcm.googleapis.com/',
    'https://fcm.googleapis.com:8443/', 'http://fcm.googleapis.com/',
    'https://fcm.googleapis.com/\nsecret', 'https://fcm.googleapis.com\\@evil.test/'])
def test_push_ssrf_rejected(endpoint):
    with pytest.raises(ValueError): validate_push_endpoint(endpoint)


@pytest.mark.parametrize('endpoint', ['https://fcm.googleapis.com/fcm/send/abc',
    'https://updates.push.services.mozilla.com/wpush/v2/abc',
    'https://web.push.apple.com/abc', 'https://wns2.notify.windows.com/abc'])
def test_push_vendor_endpoints(endpoint):
    assert validate_push_endpoint(endpoint) == endpoint


def test_push_redirects_disabled():
    with patch('requests.Session.request', return_value='ok') as request:
        assert PushSession().post('https://fcm.googleapis.com/test', allow_redirects=True) == 'ok'
        assert request.call_args.kwargs['allow_redirects'] is False


@pytest.mark.parametrize('filename', ['../../outside.wav', '/tmp/outside.wav', 'C:\\temp\\outside.wav', 'normal.wav'])
def test_upload_cannot_choose_destination(tmp_path, monkeypatch, filename):
    monkeypatch.setattr(audio_processor, 'VOICE_UPLOAD_DIR', str(tmp_path / 'uploads'))
    monkeypatch.setattr(audio_processor, 'TTS_OUTPUT_DIR', str(tmp_path / 'outputs'))
    result = Path(asyncio.run(voice._save_upload(UploadFile(filename=filename, file=io.BytesIO(b'RIFF audio')))))
    assert result.parent == tmp_path / 'uploads'
    assert result.name != 'outside.wav'
    assert result.read_bytes() == b'RIFF audio'


@pytest.mark.parametrize('filename,data,status', [('bad.py', b'code', 400), ('empty.wav', b'', 400),
    ('big.wav', b'a' * (audio_processor.MAX_AUDIO_BYTES + 1), 413)], ids=['unsupported', 'empty', 'oversized'])
def test_bad_upload_rejected(filename, data, status):
    with pytest.raises(HTTPException) as exc:
        asyncio.run(voice._save_upload(UploadFile(filename=filename, file=io.BytesIO(data))))
    assert exc.value.status_code == status


def test_scan_read_is_bounded():
    upload = SimpleNamespace(read=AsyncMock(return_value=b'a' * (scan.MAX_UPLOAD_SIZE + 1)))
    with pytest.raises(HTTPException) as exc: asyncio.run(scan._read_and_validate_bytes(upload))
    assert exc.value.status_code == 413
    upload.read.assert_awaited_once_with(scan.MAX_UPLOAD_SIZE + 1)


def test_admin_rejected_before_ingestion():
    app = FastAPI()
    app.include_router(admin.router)
    client = TestClient(app)
    assert client.post('/admin/ingest-schemes').status_code == 401
    assert client.post('/admin/ingest-schemes', headers=headers()).status_code == 403


def test_protected_voice_and_sensor_routes():
    app = FastAPI()
    app.include_router(voice.router, dependencies=[Depends(authenticated_user)])
    app.include_router(sensor.router)
    client = TestClient(app)
    assert client.post('/voice/upload', files={'file': ('x.wav', b'a')}).status_code == 401
    assert client.get('/sensor-data/latest/alice').status_code == 401
    assert client.get('/sensor-data/latest/bob', headers=headers()).status_code == 403
    assert client.get('/sensor-data/analysis/bob', headers=headers()).status_code == 403
    assert client.get('/sensor-data/live', headers=headers()).status_code == 403


def test_redis_initialized_after_import_and_forwarded_header_ignored(monkeypatch):
    from starlette.requests import Request
    calls = []
    class Pipeline:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        def incr(self, key): calls.append(key)
        def expire(self, *args, **kwargs): pass
        async def execute(self): return [11, True]
    monkeypatch.setattr(rate_limiter.session_store, 'redis_client', SimpleNamespace(pipeline=lambda **kw: Pipeline()))
    request = Request({'type': 'http', 'method': 'POST', 'path': '/chat',
        'headers': [(b'x-forwarded-for', b'forged')], 'client': ('actual-peer', 1)})
    with pytest.raises(HTTPException) as exc: asyncio.run(rate_limiter.rate_limit(request))
    assert exc.value.status_code == 429
    assert calls == ['rate_limit:actual-peer:/chat']


def test_local_rate_limit_when_redis_unavailable(monkeypatch):
    from starlette.requests import Request
    monkeypatch.setattr(rate_limiter.session_store, 'redis_client', None)
    request = Request({'type': 'http', 'method': 'POST', 'path': '/chat', 'headers': [], 'client': ('peer', 1)})
    for _ in range(60): asyncio.run(rate_limiter.rate_limit(request))
    with pytest.raises(HTTPException) as exc: asyncio.run(rate_limiter.rate_limit(request))
    assert exc.value.status_code == 429


@pytest.mark.parametrize('owner,accepted', [('victim', False), ('alice', True)])
def test_websocket_conversation_ownership(monkeypatch, owner, accepted):
    class Session:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
    manager = SimpleNamespace(connect=AsyncMock(), disconnect=AsyncMock())
    monkeypatch.setattr(chat_ws, 'manager', manager)
    monkeypatch.setattr(chat_ws, 'AsyncSessionLocal', Session)
    monkeypatch.setattr(chat_ws.ConversationRepository, 'get_by_id', AsyncMock(return_value=SimpleNamespace(userId=owner)))
    app = FastAPI()
    app.include_router(chat_ws.router)
    with TestClient(app).websocket_connect('/chat?session_id=known-id&token=' + token()) as ws:
        if not accepted: assert ws.receive_json()['detail'] == 'Conversation not found'
    assert manager.connect.await_count == int(accepted)
    assert manager.disconnect.await_count == int(accepted)


def test_stale_disconnect_preserves_new_socket():
    async def run():
        manager = ConnectionManager()
        first, second = object(), object()
        await manager.connect('alice', 'chat', first)
        await manager.connect('alice', 'chat', second)
        await manager.disconnect('alice', 'chat', first)
        assert manager.active_connections['chat'] is second
    asyncio.run(run())


def test_main_registers_authenticated_routes_and_production_errors(monkeypatch):
    import sys
    # Optional provider is deliberately mocked; this test exercises routing.
    monkeypatch.setitem(sys.modules, 'app.integrations.supabase.supabase_store',
                        SimpleNamespace(SupabaseStore=lambda: SimpleNamespace(client=None)))
    from app.main import app
    from app.api.http import chat
    monkeypatch.setattr(chat.agent_service, 'chat', AsyncMock(return_value={'content': 'safe reply'}))
    client = TestClient(app, raise_server_exceptions=False)
    for path, payload in [('/api/chat/agent', {'messages': []}),
                          ('/api/chat/generate', {'message': 'hello'}),
                          ('/geo/analyze', {'latitude': 10, 'longitude': 20})]:
        assert client.post(path, json=payload).status_code == 401
    assert client.post('/api/chat/generate', json={'message': 'hello'}, headers=headers()).json()['response'] == 'safe reply'
    assert app.debug is False


def test_body_limit_before_parsing_and_on_chunked_requests():
    from app.middleware.body_limit import BodySizeLimit
    from fastapi import Request
    app = FastAPI()
    app.add_middleware(BodySizeLimit, max_bytes=8)
    @app.post('/body')
    async def body(request: Request):
        return {'bytes': len(await request.body())}
    client = TestClient(app)
    assert client.post('/body', content=b'1234').json() == {'bytes': 4}
    assert client.post('/body', content=b'123456789').status_code == 413
    assert client.post('/body', content=iter([b'12345', b'67890'])).status_code == 413
