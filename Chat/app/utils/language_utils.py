SUPPORTED_LANGUAGES = {
    "ta": "Tamil",
    "ml": "Malayalam",
    "hi": "Hindi",
    "en": "English",
}


def is_supported_language(code: str) -> bool:
    return code in SUPPORTED_LANGUAGES


def normalize_language_code(code: str) -> str:
    code = code.lower().strip()
    if code in SUPPORTED_LANGUAGES:
        return code
    return "en"


def get_language_name(code: str) -> str:
    return SUPPORTED_LANGUAGES.get(code, "English")
