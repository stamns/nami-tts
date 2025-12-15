from __future__ import annotations

from typing import Any, Dict, Optional

from backend.nano_tts import NanoAITTS
from backend.tts_providers.base import ProviderHealth, TTSProvider


class NanoAIProvider(TTSProvider):
    name = "nanoai"

    def __init__(self, api_key: Optional[str] = None, **kwargs: Any):
        super().__init__(api_key=api_key, **kwargs)
        self._engine = NanoAITTS()

    @property
    def engine(self) -> NanoAITTS:
        return self._engine

    def get_models(self) -> Dict[str, str]:
        self._engine.load_voices()
        return {tag: info.get("name", tag) for tag, info in (self._engine.voices or {}).items()}

    def generate_audio(self, text: str, model: str, **options: Any) -> bytes:
        timeout = int(options.get("timeout") or self._engine.http_timeout or 60)
        retry_count = int(options.get("retry_count") or self._engine.retry_count or 2)
        speed = float(options.get("speed") or 1.0)
        pitch = float(options.get("pitch") or 1.0)
        volume = float(options.get("volume") or 1.0)
        language = options.get("language")
        gender = options.get("gender")
        return self._engine.get_audio(
            text,
            voice=model,
            speed=speed,
            pitch=pitch,
            volume=volume,
            language=language,
            gender=gender,
            timeout=timeout,
            retry_count=retry_count
        )

    def health_check(self) -> ProviderHealth:
        try:
            models = self.get_models()
            ok = bool(models)
            return ProviderHealth(ok=ok, message="ok" if ok else "no voices loaded")
        except Exception as e:
            return ProviderHealth(ok=False, message=str(e))
