"""TTS provider implementations.

Providers should implement :class:`backend.tts_providers.base.TTSProvider`.
"""

from .base import TTSProvider
from .nanoai import NanoAIProvider
from .google import GoogleTTSProvider
from .azure import AzureTTSProvider

__all__ = [
    "TTSProvider",
    "NanoAIProvider",
    "GoogleTTSProvider",
    "AzureTTSProvider",
]
