"""Compatibility entrypoint.

Vercel and local scripts historically import `app` from `app.py`.
The main implementation now lives in :mod:`backend.app`.
"""

from backend.app import app, main

__all__ = ["app"]


if __name__ == "__main__":
    main()
