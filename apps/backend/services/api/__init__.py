"""Nova API facade — thin HTTP/WebSocket layer over existing services."""

from .app import create_app

__all__ = ["create_app"]
