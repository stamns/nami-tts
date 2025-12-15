from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ProviderHealth:
    ok: bool
    message: str = ""
    details: Optional[Dict[str, Any]] = None


class TTSProvider:
    """TTS provider abstract base class."""

    name: str

    def __init__(self, api_key: Optional[str] = None, **kwargs: Any):
        self.api_key = api_key
        self.config: Dict[str, Any] = dict(kwargs)

    def get_models(self) -> Dict[str, str]:
        """Return a mapping of model_id -> human readable description."""

        raise NotImplementedError

    def generate_audio(self, text: str, model: str, **options: Any) -> bytes:
        """Generate audio bytes."""

        raise NotImplementedError

    def health_check(self) -> ProviderHealth:
        """Return provider health information."""

        raise NotImplementedError
