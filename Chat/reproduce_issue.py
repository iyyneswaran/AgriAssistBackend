import asyncio
import sys
import os
import logging

# Configure logging to see the error output from chat_service
logging.basicConfig(level=logging.ERROR)

# Add the current directory to sys.path to allow imports from app
sys.path.append(os.getcwd())

try:
    from app.services.chat.chat_service import generate_ai_response, call_gemini
except ImportError as e:
    print(f"ImportError: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"sys.path: {sys.path}")
    sys.exit(1)

async def main():
    print("Testing generate_ai_response...")
    try:
        # We can try calling call_gemini directly first to isolate the issue
        print("Calling call_gemini directly...")
        response = await call_gemini("Test prompt for paddy fertilizer")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Exception calling call_gemini: {e}")

    print("\nTesting generate_ai_response full flow...")
    try:
        response = await generate_ai_response(
            user_id="test_user",
            session_id="test_session",
            language="English",
            content="What fertilizer is best for paddy?"
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Exception calling generate_ai_response: {e}")

if __name__ == "__main__":
    asyncio.run(main())
