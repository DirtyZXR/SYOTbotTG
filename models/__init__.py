from database.base import Base
from .user import User
from .document import Document
from .test import Test
from .test_result import TestResult

__all__ = ["User", "Document", "Test", "TestResult"]
