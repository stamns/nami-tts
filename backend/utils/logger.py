from __future__ import annotations

import logging
import os


def setup_logging(default_name: str = "nami-tts") -> logging.Logger:
    level_name = (os.getenv("LOG_LEVEL") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    return logging.getLogger(default_name)
