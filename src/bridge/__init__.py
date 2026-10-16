"""PySide6 objects and models exposed to QML (``import PokerPractice.Bridge``).

Kept thin: no poker rules live here.
"""

from bridge import registry
from bridge.app_bridge import AppBridge

__all__ = ["AppBridge", "registry"]
