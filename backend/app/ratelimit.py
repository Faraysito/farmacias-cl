"""Limiter compartido por toda la app (slowapi)."""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import RATE_LIMIT_DEFAULT

limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT_DEFAULT])
