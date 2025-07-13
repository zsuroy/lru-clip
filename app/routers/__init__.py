"""
API routers for CLIP.LRU
"""

from .auth import router as auth_router
from .clips import router as clips_router
from .files import router as files_router
from .admin import router as admin_router

__all__ = ["auth_router", "clips_router", "files_router", "admin_router"]
