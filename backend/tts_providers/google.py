from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, Optional

from gtts import gTTS
from gtts.lang import tts_langs

from backend.tts_providers.base import ProviderHealth, TTSProvider


class GoogleTTSProvider(TTSProvider):
    name = "google"

    def __init__(self, api_key: Optional[str] = None, **kwargs: Any):
        super().__init__(api_key=api_key, **kwargs)

    def get_models(self) -> Dict[str, str]:
        langs = tts_langs()
        return {code: name for code, name in langs.items()}

    def generate_audio(self, text: str, model: str, **options: Any) -> bytes:
        if not text or not text.strip():
            raise ValueError("text is empty")

        language = (options.get("language") or model or "en").strip()
        if language.startswith("gtts:"):
            language = language.split(":", 1)[1]

        speed = options.get("speed")
        slow = False
        if speed is not None:
            try:
                slow = float(speed) < 1.0
            except Exception:
                slow = False

        fp = BytesIO()
        tts = gTTS(text=text, lang=language, slow=slow)
        tts.write_to_fp(fp)
        return fp.getvalue()

    def health_check(self) -> ProviderHealth:
        try:
            count = len(tts_langs())
            return ProviderHealth(ok=count > 0, message="ok", details={"languages": count})
        except Exception as e:
            return ProviderHealth(ok=False, message=str(e))
