from app.services.chat.context_builder import build_context
from app.core.config import settings
import httpx
import logging
import re

logger = logging.getLogger(__name__)


async def call_sarvam_llm(prompt: str) -> str:
    """
    Calls Sarvam AI's standard conversational LLM (sarvam-m) for reasoning.
    """
    system_prompt = (
        "You are AgriAssist, a friendly and knowledgeable AI assistant for Indian farmers. "
        "You help with crop advice, pest management, soil health, weather guidance, and government schemes. "
        "Keep your answers clear, short, and practical — like talking to a fellow farmer. "
        "IMPORTANT: You MUST respond in the EXACT SAME LANGUAGE as the user's question! "
        "Use bullet points when listing steps or tips. Always be encouraging and supportive."
    )

    api_key = settings.SARWAM_API_KEY
    if not api_key:
        logger.error("SARWAM_API_KEY is not configured.")
        return "I'm having trouble connecting to my brain because the API key is missing. Please contact support."

    url = "https://api.sarvam.ai/v1/chat/completions"
    payload = {
        "model": "sarvam-m",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
    }
    
    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": api_key
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            # Sarvam-m might return <think> blocks. Strip them out.
            cleaned_content = re.sub(r'<think>.*?</think>\s*', '', content, flags=re.DOTALL)
            # Failsafe if it didn't use a closing tag
            cleaned_content = cleaned_content.replace('<think>\n', '').replace('<think>', '').strip()
            # If the response was entirely inside quotes, strip them
            if cleaned_content.startswith('"') and cleaned_content.endswith('"'):
                cleaned_content = cleaned_content[1:-1].strip()

            return cleaned_content
    except httpx.TimeoutException:
        logger.error("Sarvam LLM timeout")
        return "Sorry, the AI is taking too long to respond. Please try again."
    except Exception as e:
        logger.error(f"Sarvam LLM error: {type(e).__name__}: {e}")
        return "Sorry, I couldn't process your request right now. Please try again in a moment."


async def generate_ai_response(
    user_id: str,
    session_id: str,
    language: str,
    content: str,
) -> str:
    """
    Generates an AI response for the user's chat message.
    """
    # Build context prompt with farm data
    enriched_prompt = await build_context(
        crop="Paddy",
        temperature=34,
        moisture="Low",
        weather="No rain forecast",
        user_question=content,
    )

    # Call Sarvam AI
    response = await call_sarvam_llm(enriched_prompt)
    return response
