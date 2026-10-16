"""Application-level QObject exposed to QML as the ``App`` singleton."""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtQml import QmlNamedElement, QmlSingleton, QQmlEngine

from bridge.registry import QML_IMPORT_MAJOR_VERSION, QML_IMPORT_NAME, singleton_instance
from services.paths import user_data_dir

__all__ = ["AppBridge", "QML_IMPORT_NAME", "QML_IMPORT_MAJOR_VERSION"]

APP_NAME = "Hold'em Practice"
APP_VERSION = "0.1.0"


@QmlNamedElement("App")
@QmlSingleton
class AppBridge(QObject):
    """Static application information and app-wide commands."""

    quitRequested = Signal()
    animationsEnabledChanged = Signal(bool)
    analysisModeChanged = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._animations_enabled = True
        self._analysis_mode = False

    @staticmethod
    def create(engine: QQmlEngine) -> "AppBridge":
        return singleton_instance(AppBridge)

    @Property(str, constant=True)
    def name(self) -> str:
        return APP_NAME

    @Property(str, constant=True)
    def version(self) -> str:
        return APP_VERSION

    @Property(str, constant=True)
    def dataDirectory(self) -> str:
        return str(user_data_dir())

    def _get_animations_enabled(self) -> bool:
        return self._animations_enabled

    def _set_animations_enabled(self, enabled: bool) -> None:
        if enabled != self._animations_enabled:
            self._animations_enabled = enabled
            self.animationsEnabledChanged.emit(enabled)

    animationsEnabled = Property(
        bool, _get_animations_enabled, _set_animations_enabled, notify=animationsEnabledChanged
    )

    def _get_analysis_mode(self) -> bool:
        return self._analysis_mode

    def _set_analysis_mode(self, enabled: bool) -> None:
        if enabled != self._analysis_mode:
            self._analysis_mode = enabled
            self.analysisModeChanged.emit(enabled)

    # Show opponents' reasoning after each hand.
    analysisMode = Property(bool, _get_analysis_mode, _set_analysis_mode, notify=analysisModeChanged)

    @Slot()
    def requestQuit(self) -> None:
        self.quitRequested.emit()
