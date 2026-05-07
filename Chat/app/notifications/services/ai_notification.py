"""
AI Notification Service
========================
Uses Sarvam AI (primary) or Gemini (fallback) to transform structured
events into farmer-friendly, human-readable notifications.

AI is ONLY used for summarization and language simplification.
All decisions are made by the deterministic Rule Engine.
"""

import logging
from typing import Optional

import httpx

from app.core.config import settings
from app.notifications.models.notification_event import NotificationEvent

logger = logging.getLogger(__name__)

# Notification title templates (fallback when AI is unavailable)
TITLE_TEMPLATES = {
    "smart_irrigation": "💧 Irrigation Update",
    "disease_warning": "🦠 Disease Alert",
    "drought_intelligence": "☀️ Drought Warning",
    "flood_prevention": "🌊 Flood Risk Alert",
    "resource_optimization": "♻️ Efficiency Tip",
    "iot_offline": "📡 Sensor Offline",
}

SEVERITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
    "info": "ℹ️",
}


class AINotificationService:
    """
    Transforms structured notification events into human-friendly messages.
    Uses Sarvam AI for summarization with Gemini as fallback.
    """

    async def generate_notification_text(
        self,
        event: NotificationEvent,
        language: str = "en",
    ) -> tuple[str, str, bool]:
        """
        Generate a title and body for a notification event.

        Returns:
            tuple of (title, body, ai_generated)
        """
        # Try AI summarization first
        try:
            title, body = await self._ai_summarize(event, language)
            if title and body:
                return title, body, True
        except Exception as e:
            logger.warning(f"AI summarization failed, using template: {e}")

        # Fallback to template-based generation
        title, body = self._template_fallback(event)
        return title, body, False

    async def _ai_summarize(
        self, event: NotificationEvent, language: str
    ) -> tuple[Optional[str], Optional[str]]:
        """Use Sarvam AI or Gemini to generate farmer-friendly text."""

        prompt = self._build_summarization_prompt(event, language)

        # Try Sarvam AI first
        if settings.SARWAM_API_KEY:
            result = await self._call_sarvam(prompt)
            if result:
                return result

        # Fallback to Gemini
        if settings.GEMINI_API_KEY:
            result = await self._call_gemini(prompt)
            if result:
                return result

        return None, None

    def _build_summarization_prompt(
        self, event: NotificationEvent, language: str
    ) -> str:
        """Build the prompt for AI summarization."""
        lang_instruction = ""
        if language == "ta":
            lang_instruction = (
                "Write the notification in Tamil (தமிழ்) using simple, "
                "conversational language that a farmer would understand. "
            )
        elif language != "en":
            lang_instruction = f"Write in {language} language. "

        return f"""You are an agricultural notification assistant. Convert this structured alert into a short, friendly push notification for a farmer.

{lang_instruction}

RULES:
- Title: maximum 50 characters, clear and actionable
- Body: maximum 150 characters, explain what happened and what to do
- No technical jargon
- Be warm and helpful, not alarming
- Focus on what the farmer should DO

STRUCTURED ALERT:
- Type: {event.event_type}
- Severity: {event.severity}
- Situation: {event.situation}
- Impact: {event.impact}
- Recommended Action: {event.recommended_action}

Respond EXACTLY in this format:
TITLE: <notification title>
BODY: <notification body>"""

    async def _call_sarvam(self, prompt: str) -> Optional[tuple[str, str]]:
        """Call Sarvam AI API for summarization."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.sarvam.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.SARWAM_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "sarvam-m",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 200,
                        "temperature": 0.3,
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    text = data["choices"][0]["message"]["content"]
                    return self._parse_ai_response(text)
        except Exception as e:
            logger.warning(f"Sarvam AI call failed: {e}")
        return None

    async def _call_gemini(self, prompt: str) -> Optional[tuple[str, str]]:
        """Call Gemini API for summarization."""
        try:
            from google import genai

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
            if response and response.text:
                return self._parse_ai_response(response.text)
        except Exception as e:
            logger.warning(f"Gemini call failed: {e}")
        return None

    def _parse_ai_response(self, text: str) -> Optional[tuple[str, str]]:
        """Parse TITLE/BODY from AI response."""
        title = None
        body = None
        for line in text.strip().split("\n"):
            line = line.strip()
            if line.upper().startswith("TITLE:"):
                title = line[6:].strip()
            elif line.upper().startswith("BODY:"):
                body = line[5:].strip()

        if title and body:
            return title[:100], body[:300]
        return None

    def _template_fallback(self, event: NotificationEvent) -> tuple[str, str]:
        """Generate notification text from templates (no AI)."""
        severity_emoji = SEVERITY_EMOJI.get(event.severity, "")
        title = f"{severity_emoji} {TITLE_TEMPLATES.get(event.event_type, 'Farm Alert')}"

        # Build concise body from structured data
        body = event.situation
        if len(body) > 120:
            body = body[:117] + "..."

        if event.recommended_action:
            action_short = event.recommended_action
            if len(action_short) > 80:
                action_short = action_short[:77] + "..."
            body = f"{body} → {action_short}"

        if len(body) > 200:
            body = body[:197] + "..."

        return title, body
