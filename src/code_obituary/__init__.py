"""
code-obituary: Write AI-generated obituaries for deleted code.

Because every function deserves a proper farewell.
"""

__version__ = "0.1.0"
__author__ = "sravyalu"

from .analyzer import generate_obituary
from .graveyard import append_obituary, list_obituaries

__all__ = ["generate_obituary", "append_obituary", "list_obituaries"]
