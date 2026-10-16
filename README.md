# Poker For Practice

A Texas Hold'em practice application for Windows built with Python, PySide6 and Qt Quick/QML.
**Virtual chips only** — there is no real-money gambling, deposits or withdrawals.

> Status: Phase 1 (application skeleton). The poker engine, gameplay, opponents and
> persistence are implemented in later phases.

## Requirements

- Python 3.12+
- PySide6 6.12 (installed from `requirements.txt`)

## Setup

```bash
python -m venv .venv            # Python 3.12+
# Windows:  .venv\Scripts\activate
# Linux:    source .venv/bin/activate
pip install -r requirements-dev.txt
```

If the system Python is older than 3.12, [uv](https://docs.astral.sh/uv/) can provide one:

```bash
uv python install 3.12
uv venv --python 3.12 .venv
uv pip install --python .venv -r requirements-dev.txt
```

## Running

```bash
python main.py
```

User data (logs; later the SQLite database) is stored outside the installation folder:

| Platform | Location |
| --- | --- |
| Windows | `%APPDATA%\PokerPractice` |
| Linux | `$XDG_DATA_HOME/PokerPractice` (default `~/.local/share/PokerPractice`) |
| macOS | `~/Library/Application Support/PokerPractice` |

Set `POKER_PRACTICE_DATA_DIR` to use another directory (tests do this automatically).

## Testing

```bash
python -m pytest
```

Tests run headless (`QT_QPA_PLATFORM=offscreen` is set in `tests/conftest.py`).

### Screenshots for visual QA

```bash
python tools/screenshot.py out_dir --sizes 1024x640,1920x1080 --screens menu,table
```

Renders each screen offscreen at each size and exits non-zero if QML reported warnings.

## Project layout

```
main.py              entry point
src/poker/           cards, deck, hand evaluation, betting, pots, game state (UI-independent)
src/ai/              computer opponent strategies
src/services/        application bootstrap, paths, logging; later controller, persistence, statistics
src/bridge/          QObjects/models exposed to QML (import PokerPractice.Bridge)
qml/Main.qml         application window and screen navigation
qml/components/      Theme singleton and reusable controls (cards, chips, seats in later phases)
qml/screens/         main menu, table, statistics, hand history, settings
assets/              bundled visual resources
tests/               pytest suite
tools/               developer utilities
docs/                architecture notes
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for design decisions.

## Troubleshooting

- **Blank window or startup failure:** check the log file in `<data dir>/logs/poker_practice.log`;
  QML errors are forwarded there.
- **Linux: `Could not load the Qt platform plugin "xcb"`:** install the system package
  `libxcb-cursor0`.
