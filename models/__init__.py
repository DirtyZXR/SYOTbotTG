# Сначала импортируем Base из database.base
from database.base import Base

# Затем импортируем модели, которые используют Base
from .user import User
from .document import Document
from .test import Test
from .test_result import TestResult
from .settings import Settings

__all__ = ["User", "Settings", "Document", "Test", "TestResult"]
