from __future__ import annotations

from typing import Any, Dict, Optional

from backend.tts_providers.base import ProviderHealth, TTSProvider


class BaiduTTSProvider(TTSProvider):
    name = "baidu"

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        secret_key: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(api_key=api_key, **kwargs)
        self.secret_key = secret_key or self.config.get("secret_key")

    def get_models(self) -> Dict[str, str]:
        return {}

    def generate_audio(self, text: str, model: str, **options: Any) -> bytes:
        raise NotImplementedError("Baidu TTS provider is not implemented in this repository yet")

    def health_check(self) -> ProviderHealth:
        if not self.api_key or not self.secret_key:
            return ProviderHealth(ok=False, message="BAIDU_API_KEY/BAIDU_SECRET_KEY not configured")
        return ProviderHealth(ok=False, message="not implemented")
