from __future__ import annotations

from typing import Any, Dict, Optional
from xml.sax.saxutils import escape

import requests

from backend.tts_providers.base import ProviderHealth, TTSProvider


class AzureTTSProvider(TTSProvider):
    name = "azure"

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        region: Optional[str] = None,
        endpoint: Optional[str] = None,
        default_voice: str = "en-US-AriaNeural",
        **kwargs: Any,
    ):
        super().__init__(api_key=api_key, **kwargs)
        self.region = region or self.config.get("region")
        self.endpoint = endpoint or self.config.get("endpoint")
        self.default_voice = default_voice

    def _tts_endpoint(self) -> str:
        if self.endpoint:
            return self.endpoint.rstrip("/")
        if not self.region:
            raise ValueError("AZURE_REGION or AZURE_ENDPOINT is required")
        return f"https://{self.region}.tts.speech.microsoft.com"

    def get_models(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        if not (self.region or self.endpoint):
            return {}

        base = self._tts_endpoint()
        url = f"{base}/cognitiveservices/voices/list"
        resp = requests.get(url, headers={"Ocp-Apim-Subscription-Key": self.api_key}, timeout=10)
        resp.raise_for_status()
        voices = resp.json()
        models: Dict[str, str] = {}
        for v in voices:
            short = v.get("ShortName")
            if not short:
                continue
            locale = v.get("Locale") or ""
            gender = v.get("Gender") or ""
            display = v.get("DisplayName") or ""
            models[short] = " ".join(x for x in [display, locale, gender] if x).strip() or short
        return models

    def generate_audio(self, text: str, model: str, **options: Any) -> bytes:
        if not self.api_key:
            raise ValueError("AZURE_API_KEY is not configured")

        voice = (model or self.default_voice).strip() or self.default_voice
        base = self._tts_endpoint()
        url = f"{base}/cognitiveservices/v1"

        lang = options.get("language")
        xml_lang = (lang or "en-US").strip()

        ssml = (
            f"<speak version='1.0' xml:lang='{escape(xml_lang)}'>"
            f"<voice name='{escape(voice)}'>{escape(text)}</voice>"
            "</speak>"
        )

        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
            "User-Agent": "nami-tts",
        }

        resp = requests.post(url, data=ssml.encode("utf-8"), headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.content

    def health_check(self) -> ProviderHealth:
        if not self.api_key:
            return ProviderHealth(ok=False, message="AZURE_API_KEY not configured")

        if not (self.region or self.endpoint):
            return ProviderHealth(ok=False, message="AZURE_REGION/AZURE_ENDPOINT not configured")

        return ProviderHealth(ok=True, message="configured")
