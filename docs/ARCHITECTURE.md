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

## Poker engine (`src/poker`)

| Module | Responsibility |
| --- | --- |
| `cards.py` | `Rank`, `Suit`, immutable `Card`, parsing (`"As"`), `FULL_DECK` |
| `deck.py` | Seeded shuffle; dealing can never repeat a card; `Deck.stacked()` for deterministic scenarios/replays |
| `evaluator.py` | `evaluate()` 5–7 cards → comparable `HandValue(category, tiebreak)`; `best_five()` for highlighting; `describe()` |
| `pots.py` | `build_pots()` layers contributions into main/side pots; `award_pots()` with split and odd-chip handling |
| `actions.py` | `Action` (BET/RAISE amounts are *raise-to* street totals), `LegalActions` |
| `events.py` | Immutable event records — the single source for history, statistics and UI sequencing |
| `hand.py` | `HoldemHand` state machine for one hand |
| `table.py` | `Table`: stacks between hands, button rotation, blind levels, session reset |

All chip amounts are `int`. `HoldemHand` verifies chip conservation when it distributes the pot.

### Rules as implemented

- **Positions:** heads-up, the button posts the small blind and acts first pre-flop, last afterwards.
  Otherwise SB/BB are the next two seats after the button. Pre-flop action starts after the BB;
  later streets start with the first active player after the button.
- **Button:** "moving button" — it advances to the next seat with chips; busted seats are
  skipped and there are no dead blinds. (Simpler than the dead-button rule, standard for
  practice/home games.)
- **Short blinds:** a player who cannot cover a blind posts all they have and is all-in; the
  amount to call remains the full big blind (excess is returned as an uncalled bet).
- **Minimum bet** is the big blind. **Minimum raise:** the bet must grow by at least the
  largest bet/raise increment of the street.
- **Incomplete all-in raises** (smaller than a minimum raise) do not reopen betting for players
  who already acted. Several short all-ins that together amount to a full raise since a
  player's last action *do* reopen it for that player (TDA-style cumulative rule).
- A player cannot raise when every opponent is all-in (call or fold only).
- **Uncalled chips** are returned at the end of each street and when a hand ends by folds.
- **Run-outs:** when fewer than two players can still bet, remaining streets are dealt
  (with burns) without action and the hand goes to showdown.
- **Split pots:** each pot is split evenly among the best hands eligible for it; leftover
  chips go one at a time to winners in seat order starting left of the button.
- **Duplicate submissions:** `act(..., expected_action_count=n)` rejects actions prepared for a
  decision point that has already passed (`StaleActionError`). Acting out of turn, after the
  hand ended, or with an illegal amount raises `IllegalActionError`/`HandStateError` without
  changing state.
- Folding is always permitted when it is the player's turn (the UI may ask for confirmation
  when checking is free).

### Testing approach

- Deterministic scenarios use `tests/poker_helpers.make_hand()`, which stacks the deck in real
  dealing order so hole cards and boards are specified exactly.
- The evaluator is cross-checked against an independent brute-force 5-card reference on
  thousands of random 5/6/7-card hands.
- Randomized sessions (seeded) play hundreds of hands with random legal actions and assert
  chip conservation after every action, no negative stacks, no duplicate cards, pot awards
  equal to contributions and zero-sum results.
