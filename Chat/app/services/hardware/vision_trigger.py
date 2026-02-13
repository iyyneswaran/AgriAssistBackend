from app.services.chat.chat_service import generate_ai_response
from app.services.hardware.call_service import initiate_ai_voice_call


async def handle_vision_event(
    farmer_id: str,
    phone_number: str,
    detected_disease: str,
    crop: str,
    language: str,
) -> dict:
    """
    Triggered when YOLO detects a disease from ESP32 camera.
    Generates AI advice and initiates voice call.
    """

    system_message = (
        f"Disease detected: {detected_disease}\n"
        f"Crop: {crop}\n"
        "Provide clear treatment and prevention advice."
    )

    ai_response = await generate_ai_response(
        user_id=farmer_id,
        session_id="hardware_event",
        language=language,
        content=system_message,
    )

    call_result = await initiate_ai_voice_call(
        phone_number=phone_number,
        message_text=ai_response,
        language=language,
    )

    return {
        "status": "vision_trigger_processed",
        "disease": detected_disease,
        "ai_advice": ai_response,
        "call_details": call_result,
    }
