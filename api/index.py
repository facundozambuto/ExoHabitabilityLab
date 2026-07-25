"""
Vercel serverless entry point.

Vercel's Python runtime detects the ASGI ``app`` object exported here and
serves the FastAPI application. All routing is handled inside the app; the
`vercel.json` rewrite sends every request to this module.
"""

from app.main import app

# Vercel looks for a module-level ASGI/WSGI callable named ``app``.
__all__ = ["app"]
