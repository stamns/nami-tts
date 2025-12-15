from __future__ import annotations

from typing import Any, Dict, Optional

from backend.tts_providers.base import ProviderHealth, TTSProvider


class AliyunTTSProvider(TTSProvider):
    name = "aliyun"

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(api_key=api_key, **kwargs)
        self.access_key_id = access_key_id or self.config.get("access_key_id")
        self.access_key_secret = access_key_secret or self.config.get("access_key_secret")

    def get_models(self) -> Dict[str, str]:
        return {}

    def generate_audio(self, text: str, model: str, **options: Any) -> bytes:
        raise NotImplementedError("Aliyun TTS provider is not implemented in this repository yet")

    def health_check(self) -> ProviderHealth:
        if not self.access_key_id or not self.access_key_secret:
            return ProviderHealth(ok=False, message="ALIYUN_ACCESS_KEY_ID/ALIYUN_ACCESS_KEY_SECRET not configured")
        return ProviderHealth(ok=False, message="not implemented")
