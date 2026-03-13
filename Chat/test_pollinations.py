import asyncio
import httpx

async def test():
    payload = {
        'messages': [
            {'role': 'system', 'content': 'You are AgriAssist, an AI for farmers. You must respond in the Tamil language.'},
            {'role': 'user', 'content': 'What is the best fertilizer for paddy?'}
        ],
        'model': 'openai'
    }
    # It might need timeout
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post('https://text.pollinations.ai/openai', json=payload)
        print("Status:", res.status_code)
        print("Response:", res.json()['choices'][0]['message']['content'])

if __name__ == '__main__':
    asyncio.run(test())
