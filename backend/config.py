from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from backend.tts_providers.aliyun import AliyunTTSProvider
from backend.tts_providers.azure import AzureTTSProvider
from backend.tts_providers.baidu import BaiduTTSProvider
from backend.tts_providers.google import GoogleTTSProvider
from backend.tts_providers.nanoai import NanoAIProvider
from backend.tts_providers.base import TTSProvider


def _split_csv(value: str) -> List[str]:
    return [x.strip().lower() for x in value.split(",") if x.strip()]


@dataclass
class ProviderAttemptError:
    provider: str
    error: str


class TTSManager:
    """TTS provider manager with priority + fallback."""

    def __init__(
        self,
        *,
        default_provider: str = "nanoai",
        priority_order: Optional[List[str]] = None,
        models_cache_ttl_seconds: int = 2 * 60 * 60,
    ):
        self.providers: Dict[str, TTSProvider] = {}
        self.default_provider = default_provider.lower().strip() or "nanoai"
        self.priority_order = priority_order or ["nanoai", "google", "azure", "baidu", "aliyun"]
        self.models_cache_ttl_seconds = models_cache_ttl_seconds

        self._models_cache: Dict[str, Tuple[float, Dict[str, str]]] = {}
        self._models_lock = threading.Lock()

    def register_provider(self, name: str, provider: TTSProvider) -> None:
        self.providers[name.lower()] = provider

    def list_provider_names(self) -> List[str]:
        return list(self.providers.keys())

    def _dedupe_keep_order(self, items: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for x in items:
            if x in seen:
                continue
            seen.add(x)
            out.append(x)
        return out

    def get_provider_candidates(self, requested: Optional[str] = None) -> List[str]:
        requested_norm = requested.lower().strip() if requested else None
        candidates: List[str] = []

        if requested_norm:
            candidates.append(requested_norm)

        if self.default_provider:
            candidates.append(self.default_provider)

        candidates.extend(self.priority_order)
        candidates.extend(self.providers.keys())

        candidates = self._dedupe_keep_order([c for c in candidates if c])
        return [c for c in candidates if c in self.providers]

    def get_provider(self, name: Optional[str] = None) -> Tuple[str, TTSProvider]:
        for candidate in self.get_provider_candidates(name):
            provider = self.providers.get(candidate)
            if provider:
                return candidate, provider
        raise KeyError("No available TTS provider")

    def get_models(
        self,
        provider_name: Optional[str] = None,
        force_refresh: bool = False,
    ) -> Tuple[str, Dict[str, str]]:
        last_error: Optional[Exception] = None

        for actual_name in self.get_provider_candidates(provider_name):
            provider = self.providers[actual_name]

            if not force_refresh:
                with self._models_lock:
                    cached = self._models_cache.get(actual_name)
                    if cached:
                        cached_at, models = cached
                        if time.time() - cached_at < self.models_cache_ttl_seconds:
                            return actual_name, models

            try:
                models = provider.get_models()
            except Exception as e:
                last_error = e
                continue

            with self._models_lock:
                self._models_cache[actual_name] = (time.time(), models)

            return actual_name, models

        if last_error:
            raise last_error
        raise KeyError("No available TTS provider")

    def generate_with_fallback(self, text: str, model: str, *, provider_name: Optional[str] = None, **options: Any) -> Tuple[str, bytes, List[ProviderAttemptError]]:
        errors: List[ProviderAttemptError] = []
        for candidate in self.get_provider_candidates(provider_name):
            provider = self.providers[candidate]
            try:
                audio = provider.generate_audio(text, model, **options)
                return candidate, audio, errors
            except Exception as e:
                errors.append(ProviderAttemptError(provider=candidate, error=str(e)))
                continue
        raise RuntimeError(f"All providers failed: {[e.__dict__ for e in errors]}")


def build_tts_manager() -> TTSManager:
    default_provider = (os.getenv("DEFAULT_TTS_PROVIDER") or "nanoai").lower().strip() or "nanoai"
    priority = _split_csv(os.getenv("TTS_PROVIDER_PRIORITY") or "nanoai,google,azure,baidu,aliyun")
    ttl = int(os.getenv("MODELS_CACHE_TTL_SECONDS") or os.getenv("CACHE_DURATION") or 2 * 60 * 60)

    manager = TTSManager(default_provider=default_provider, priority_order=priority, models_cache_ttl_seconds=ttl)

    # NanoAI (built-in)
    manager.register_provider("nanoai", NanoAIProvider())

    # Google (gTTS) does not require API key
    manager.register_provider("google", GoogleTTSProvider(api_key=os.getenv("GOOGLE_API_KEY")))

    azure_key = os.getenv("AZURE_API_KEY")
    azure_region = os.getenv("AZURE_REGION")
    azure_endpoint = os.getenv("AZURE_ENDPOINT")
    manager.register_provider(
        "azure",
        AzureTTSProvider(api_key=azure_key, region=azure_region, endpoint=azure_endpoint),
    )

    manager.register_provider(
        "baidu",
        BaiduTTSProvider(api_key=os.getenv("BAIDU_API_KEY"), secret_key=os.getenv("BAIDU_SECRET_KEY")),
    )

    manager.register_provider(
        "aliyun",
        AliyunTTSProvider(
            access_key_id=os.getenv("ALIYUN_ACCESS_KEY_ID"),
            access_key_secret=os.getenv("ALIYUN_ACCESS_KEY_SECRET"),
        ),
    )

    return manager
