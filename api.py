"""ASGI entry point: uvicorn api:app --reload"""

from src.api.app import app

__all__ = ["app"]
