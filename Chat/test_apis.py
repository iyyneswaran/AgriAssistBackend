"""
Quick test script for all AgriAssist APIs
"""
import asyncio
import httpx
import json

BASE = "http://localhost:8001"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJfMSIsInJvbGUiOiJBRE1JTiJ9.wGGy3Dj3ASf7zqpmWGrQj8jMLlErvPqmg0KY6OZlYKQ"

PASS = "[PASS]"
FAIL = "[FAIL]"

results = []


async def main():
    async with httpx.AsyncClient(timeout=15) as client:
        # ---- TEST 1: GET /docs ----
        print("=" * 60)
        print("TEST 1: GET /docs (Swagger UI)")
        print("=" * 60)
        try:
            r = await client.get(f"{BASE}/docs")
            status = PASS if r.status_code == 200 else FAIL
            ct = r.headers.get("content-type", "")
            print(f"  {status} Status: {r.status_code}, Content-Type: {ct}")
            results.append(("GET /docs", r.status_code, status))
        except Exception as e:
            print(f"  {FAIL} ERROR: {e}")
            results.append(("GET /docs", 0, FAIL))

        # ---- TEST 2: POST /api/offline/sync ----
        print()
        print("=" * 60)
        print("TEST 2: POST /api/offline/sync")
        print("=" * 60)
        try:
            payload = [
                {
                    "message_id": "m1",
                    "session_id": "s1",
                    "language": "en",
                    "content": "Hello from offline sync test",
                }
            ]
            r = await client.post(f"{BASE}/api/offline/sync", json=payload)
            status = PASS if r.status_code == 200 else FAIL
            print(f"  {status} Status: {r.status_code}")
            print(f"  Body: {r.json()}")
            results.append(("POST /api/offline/sync", r.status_code, status))
        except Exception as e:
            print(f"  {FAIL} ERROR: {e}")
            results.append(("POST /api/offline/sync", 0, FAIL))

        # ---- TEST 3: POST /api/voice/upload ----
        print()
        print("=" * 60)
        print("TEST 3: POST /api/voice/upload")
        print("=" * 60)
        try:
            files = {"file": ("test.wav", b"fake audio content", "audio/wav")}
            r = await client.post(f"{BASE}/api/voice/upload", files=files)
            status = PASS if r.status_code == 200 else FAIL
            print(f"  {status} Status: {r.status_code}")
            print(f"  Body: {r.json()}")
            results.append(("POST /api/voice/upload", r.status_code, status))
        except Exception as e:
            print(f"  {FAIL} ERROR: {e}")
            results.append(("POST /api/voice/upload", 0, FAIL))

        # ---- TEST 4: POST /api/admin/initiate-call (WITH valid token) ----
        print()
        print("=" * 60)
        print("TEST 4: POST /api/admin/initiate-call (with ADMIN token)")
        print("=" * 60)
        try:
            payload = {
                "farmer_id": "farmer_001",
                "message": "Your irrigation scheduled",
                "language": "en",
            }
            r = await client.post(
                f"{BASE}/api/admin/initiate-call?token={TOKEN}", json=payload
            )
            status = PASS if r.status_code == 200 else FAIL
            print(f"  {status} Status: {r.status_code}")
            print(f"  Body: {r.json()}")
            results.append(("POST /api/admin/initiate-call (auth)", r.status_code, status))
        except Exception as e:
            print(f"  {FAIL} ERROR: {e}")
            results.append(("POST /api/admin/initiate-call (auth)", 0, FAIL))

        # ---- TEST 5: POST /api/admin/initiate-call (NO token - expect 422) ----
        print()
        print("=" * 60)
        print("TEST 5: POST /api/admin/initiate-call (NO token - expect 422)")
        print("=" * 60)
        try:
            payload = {
                "farmer_id": "farmer_001",
                "message": "test",
                "language": "en",
            }
            r = await client.post(f"{BASE}/api/admin/initiate-call", json=payload)
            status = PASS if r.status_code in (401, 422) else FAIL
            print(f"  {status} Status: {r.status_code} (expected 401 or 422)")
            print(f"  Body: {r.json()}")
            results.append(("POST /api/admin/initiate-call (no auth)", r.status_code, status))
        except Exception as e:
            print(f"  {FAIL} ERROR: {e}")
            results.append(("POST /api/admin/initiate-call (no auth)", 0, FAIL))

    # ---- TEST 6: WebSocket /ws/chat ----
    print()
    print("=" * 60)
    print("TEST 6: WebSocket /ws/chat (with token + session_id)")
    print("=" * 60)
    try:
        from httpx_ws import aconnect_ws

        async with aconnect_ws(
            f"{BASE}/ws/chat?token={TOKEN}&session_id=test_session_1",
        ) as ws:
            await ws.send_json(
                {
                    "type": "chat_message",
                    "language": "English",
                    "content": "What fertilizer is best for paddy?",
                }
            )
            tokens_received = []
            while True:
                msg = await asyncio.wait_for(ws.receive_json(), timeout=30)
                if msg.get("type") == "ai_token":
                    tokens_received.append(msg.get("content", ""))
                elif msg.get("type") == "ai_complete":
                    break
            full_response = "".join(tokens_received)
            status = PASS if len(full_response) > 0 else FAIL
            print(f"  {status} Received {len(tokens_received)} tokens")
            print(f"  Response preview: {full_response[:200]}...")
            results.append(("WS /ws/chat", len(tokens_received), status))
    except ImportError:
        print("  [SKIP] httpx_ws not installed, testing with raw websockets")
        # Fallback: use websockets library or just test connectivity
        try:
            import websockets

            uri = f"ws://localhost:8001/ws/chat?token={TOKEN}&session_id=test_session_1"
            async with websockets.connect(uri) as ws:
                await ws.send(
                    json.dumps(
                        {
                            "type": "chat_message",
                            "language": "English",
                            "content": "What fertilizer is best for paddy?",
                        }
                    )
                )
                tokens_received = []
                while True:
                    raw = await asyncio.wait_for(ws.recv(), timeout=30)
                    msg = json.loads(raw)
                    if msg.get("type") == "ai_token":
                        tokens_received.append(msg.get("content", ""))
                    elif msg.get("type") == "ai_complete":
                        break
                full_response = "".join(tokens_received)
                status = PASS if len(full_response) > 0 else FAIL
                print(f"  {status} Received {len(tokens_received)} tokens")
                print(f"  Response preview: {full_response[:200]}...")
                results.append(("WS /ws/chat", len(tokens_received), status))
        except ImportError:
            print("  [SKIP] No websocket library available")
            results.append(("WS /ws/chat", 0, "[SKIP]"))
        except Exception as e:
            print(f"  {FAIL} ERROR: {e}")
            results.append(("WS /ws/chat", 0, FAIL))
    except Exception as e:
        print(f"  {FAIL} ERROR: {e}")
        results.append(("WS /ws/chat", 0, FAIL))

    # ---- SUMMARY ----
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, code, s in results:
        print(f"  {s} {name} -> {code}")

    passed = sum(1 for _, _, s in results if s == PASS)
    total = len(results)
    print(f"\n  {passed}/{total} tests passed")


if __name__ == "__main__":
    asyncio.run(main())
