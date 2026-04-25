"""Compatibility entrypoint.

The service is now consolidated around `lab_app.py` as the single application
definition. This module re-exports `app` so existing commands that still use
`uvicorn app:app` keep working.
"""

import os

from config import APP_HOST, APP_PORT
from lab_app import app


if __name__ == "__main__":
    os.execvp(
        "uvicorn",
        [
            "uvicorn",
            "lab_app:app",
            "--host",
            APP_HOST,
            "--port",
            str(APP_PORT),
        ],
    )
