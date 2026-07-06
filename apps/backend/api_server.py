#!/usr/bin/env python3
"""Nova API server — run alongside nova.py and dashboard.py.

    cd apps/backend && uvicorn api_server:app --port 8001

Electron, React Native, and CLI clients should talk to this process only.
"""

import os

import uvicorn

from services.api import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("NOVA_API_PORT", "8001"))
    uvicorn.run("api_server:app", host="127.0.0.1", port=port, reload=True)
