import sys
import os
import asyncio

# Add the current directory to sys.path to allow imports from app
sys.path.append(os.getcwd())

try:
    from app.core.config import settings
    from google import genai
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

def main():
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        # The SDK documentation might vary, but typically list_models is available
        # It seems the new SDK uses client.models.list()
        print("Listing models...")
        # handling pagination if needed, but for now just simple iteration
        pager = client.models.list(config={"page_size": 50}) 
        for model in pager:
            print(f"Model: {model.name}, Display Name: {model.display_name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    main()
