"""Builds the Qt application, the QML engine and the bridge objects."""

from __future__ import annotations

import logging
import signal
import sys
from dataclasses import dataclass, field

from PySide6.QtCore import QCoreApplication, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlError
from PySide6.QtQuickControls2 import QQuickStyle

from bridge import AppBridge, registry
from bridge.app_bridge import APP_NAME, APP_VERSION
from services.paths import qml_dir

log = logging.getLogger(__name__)

ORGANIZATION = "PokerPractice"
MAIN_QML = "Main.qml"


class QmlLoadError(RuntimeError):
    pass


@dataclass
class AppContext:
    """Everything that must stay alive for the duration of the UI."""

    engine: QQmlApplicationEngine
    app_bridge: AppBridge
    qml_warnings: list[str] = field(default_factory=list)


def configure_qt_application() -> None:
    """Settings that must be applied before the QGuiApplication is created."""
    QCoreApplication.setOrganizationName(ORGANIZATION)
    QCoreApplication.setApplicationName(APP_NAME)
    QCoreApplication.setApplicationVersion(APP_VERSION)
    # Basic style: fully customisable and identical on every platform.
    QQuickStyle.setStyle("Basic")


def load_ui(app: QGuiApplication) -> AppContext:
    """Create the QML engine, expose bridge objects and load the main window."""
    engine = QQmlApplicationEngine()
    context = AppContext(engine=engine, app_bridge=AppBridge(engine))

    def on_warnings(warnings: list[QQmlError]) -> None:
        for warning in warnings:
            context.qml_warnings.append(warning.toString())

    engine.warnings.connect(on_warnings)
    registry.install(context.app_bridge)
    context.app_bridge.quitRequested.connect(app.quit)

    engine.addImportPath(str(qml_dir()))
    main_qml = qml_dir() / MAIN_QML
    engine.load(QUrl.fromLocalFile(str(main_qml)))
    if not engine.rootObjects():
        details = "\n".join(context.qml_warnings) or "no diagnostics"
        raise QmlLoadError(f"Failed to load {main_qml}:\n{details}")
    log.info("Loaded %s", main_qml)
    return context


def install_quit_on_signals(app: QGuiApplication) -> QTimer:
    """Quit cleanly on Ctrl+C / SIGTERM.

    Python only runs signal handlers when the interpreter regains control, which
    never happens while Qt's event loop is idle, so a cheap timer wakes it up.
    """

    def handle(signum, _frame) -> None:
        log.info("Received signal %s, quitting", signum)
        app.quit()

    signal.signal(signal.SIGINT, handle)
    signal.signal(signal.SIGTERM, handle)
    timer = QTimer(app)
    timer.timeout.connect(lambda: None)
    timer.start(250)
    return timer


def run(argv: list[str] | None = None) -> int:
    from services.logging_setup import configure_logging

    log_file = configure_logging()
    log.info("Starting %s %s (log: %s)", APP_NAME, APP_VERSION, log_file)

    configure_qt_application()
    app = QGuiApplication(argv if argv is not None else sys.argv)
    try:
        context = load_ui(app)
    except QmlLoadError:
        log.exception("Unable to start the user interface")
        return 1

    install_quit_on_signals(app)
    exit_code = app.exec()
    log.info("Exiting with code %s", exit_code)
    del context
    return exit_code
