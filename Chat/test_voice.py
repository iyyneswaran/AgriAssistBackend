"""Use FastAPI TestClient to get the actual traceback."""
from fastapi.testclient import TestClient
import traceback

try:
    from app.main import app
    client = TestClient(app)
    
    response = client.post(
        "/api/voice/upload",
        files={"file": ("test.wav", b"fake audio content", "audio/wav")},
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    traceback.print_exc()
