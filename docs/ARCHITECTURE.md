# Architecture

## Layers

```
QML (qml/)            presentation, layout, input, animation — no poker rules
   │  properties / signals / slots / list models
bridge (src/bridge)   thin QObject adapters; converts engine state to QML-friendly data
   │
services (src/services)  application bootstrap, game controller, persistence, statistics
   │
poker (src/poker), ai (src/ai)   pure Python; no Qt imports; fully unit-testable
```

Dependencies only point downward. `poker` and `ai` never import Qt, so all rules are tested
without a GUI.

## Decisions

### Top-level packages under `src/`
The packages `poker`, `ai`, `services` and `bridge` are importable from `src/`
(`main.py` and `tests/conftest.py` add it to `sys.path`; PyInstaller will use it as `pathex`).

### QML singletons via `@QmlSingleton` + Python-owned instances
Bridge classes are registered with PySide6's `@QmlNamedElement`/`@QmlSingleton` decorators in
the `PokerPractice.Bridge` module. Each class's static `create()` returns an instance that
Python created beforehand and installed through `bridge.registry.install()`, with ownership
set to C++/Python so QML never deletes it.

`qmlRegisterSingletonInstance` was tried first and rejected: under PySide6 6.12, importing a
module registered that way makes built-in types (`Item`, `Rectangle`) unassignable to
`data` ("expected QObject"). Context properties were avoided because they are untyped and
discouraged in Qt 6.

### QML loaded from the filesystem
QML and assets are loaded from `resource_root()` — the project root in development, or
`sys._MEIPASS` in a PyInstaller bundle. This keeps QML editable without a compile step; the
packaging phase bundles `qml/` and `assets/` as data files. Compiling a `.qrc` with
`pyside6-rcc` remains an option if bundling proves fragile.

### Qt Quick Controls "Basic" style
Set before the application starts. It is fully customisable and renders identically on every
platform; the native Windows style restricts control customisation.

### User data location
`services.paths.user_data_dir()` resolves to `%APPDATA%\PokerPractice` on Windows (never
the install directory), overridable with `POKER_PRACTICE_DATA_DIR`.

### Logging
`services.logging_setup` writes a rotating log in `<data dir>/logs/` and installs a Qt message
handler so QML warnings/errors are captured. `load_ui()` also collects `QQmlEngine.warnings`
and raises `QmlLoadError` if the root window fails to load.

### Signals
`install_quit_on_signals()` quits on SIGINT/SIGTERM. A 250 ms no-op timer lets the Python
interpreter run signal handlers while Qt's event loop is idle.
