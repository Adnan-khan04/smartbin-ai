# Package initializer for API route modules
# Expose route modules so `from routes import ...` works in main.py
from . import auth
from . import classification
from . import gamification
from . import dashboard
from . import users

__all__ = [
    "auth",
    "classification",
    "gamification",
    "dashboard",
    "users",
]
