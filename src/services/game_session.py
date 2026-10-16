"""A practice session: the human against computer opponents at one table.

Pure Python (no Qt). The engine resolves actions immediately; presentation
follows the engine through a :class:`HandPresenter` cursor so the controller
can reveal events at a human pace.
"""

from __future__ import annotations

import logging
import random
from collections.abc import Callable
from dataclasses import dataclass

from ai import PassiveStrategy, Strategy, create_strategy, observe
from poker import Action, ActionType, HoldemHand, IllegalActionError, Table
from poker.events import HandEvent, PlayerActed
from services.hand_presenter import HandPresenter, action_label
from services.table_view import (
    ActionView,
    AnalysisEntry,
    BetPreset,
    TableView,
    display_slots,
)
from services.wording import says
from services.view_builder import (
    RosterSeat,
    pot_views,
    result_message,
    seat_views,
    winning_board_cards,
)

log = logging.getLogger(__name__)

HUMAN_SEAT = 0
OPPONENT_NAMES = ("Avery", "Blake", "Casey", "Drew", "Emery")
OPPONENT_STYLES = ("conservative", "balanced", "aggressive")
DIFFICULTIES = ("easy", "normal", "hard")


class SessionError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SessionConfig:
    opponents: int = 3
    starting_stack: int = 2000
    small_blind: int = 10
    big_blind: int = 20
    opponent_style: str = "mixed"  # "mixed" or one of OPPONENT_STYLES
    difficulty: str = "normal"
    human_name: str = "You"
    seed: int | None = None

    def validate(self) -> None:
        if not 1 <= self.opponents <= len(OPPONENT_NAMES):
            raise SessionError(f"Opponents must be between 1 and {len(OPPONENT_NAMES)}")
        if not 0 < self.small_blind <= self.big_blind:
            raise SessionError("Blinds must satisfy 0 < small blind <= big blind")
        if self.starting_stack < self.big_blind:
            raise SessionError("Starting stack must cover at least one big blind")
        if self.opponent_style not in ("mixed", *OPPONENT_STYLES):
            raise SessionError(f"Unknown opponent style {self.opponent_style!r}")
        if self.difficulty not in DIFFICULTIES:
            raise SessionError(f"Unknown difficulty {self.difficulty!r}")
        if not self.human_name.strip():
            raise SessionError("Player name cannot be empty")


StrategyFactory = Callable[[str, str, random.Random], Strategy]


def passive_factory(style: str, difficulty: str, rng: random.Random) -> Strategy:
    """Calling-station opponents (tests and baselines)."""
    return PassiveStrategy()


def heuristic_factory(style: str, difficulty: str, rng: random.Random) -> Strategy:
    return create_strategy(style, difficulty, rng)


def opponent_styles(config: SessionConfig, rng: random.Random) -> list[str]:
    if config.opponent_style != "mixed":
        return [config.opponent_style] * config.opponents
    # Mixed: cycle through the styles from a random starting point.
    start = rng.randrange(len(OPPONENT_STYLES))
    return [OPPONENT_STYLES[(start + i) % len(OPPONENT_STYLES)] for i in range(config.opponents)]


def bet_presets(hand: HoldemHand) -> tuple[BetPreset, ...]:
    """Common sizes for the player to act, clamped to the legal range."""
    legal = hand.legal_actions()
    if not (legal.can_bet or legal.can_raise):
        return ()
    pot_after_call = hand.total_pot + legal.call_amount
    presets: list[BetPreset] = [BetPreset("Min", legal.min_to)]
    for label, fraction in (("½ Pot", 0.5), ("¾ Pot", 0.75), ("Pot", 1.0)):
        target = hand.current_bet + round(pot_after_call * fraction)
        presets.append(BetPreset(label, max(legal.min_to, min(legal.max_to, target))))
    presets.append(BetPreset("All-in", legal.max_to))
    return tuple(presets)


def action_from_request(kind: str, amount: int) -> Action:
    try:
        action_type = ActionType(kind)
    except ValueError:
        raise SessionError(f"Unknown action {kind!r}") from None
    if action_type in (ActionType.BET, ActionType.RAISE):
        return Action(action_type, int(amount))
    return Action(action_type)


class GameSession:
    def __init__(
        self,
        config: SessionConfig,
        *,
        strategy_factory: StrategyFactory = heuristic_factory,
        rng: random.Random | None = None,
    ) -> None:
        config.validate()
        self.config = config
        self.rng = rng or random.Random(config.seed)
        players = [(config.human_name, config.starting_stack)] + [
            (OPPONENT_NAMES[i], config.starting_stack) for i in range(config.opponents)
        ]
        self.table = Table(players, config.small_blind, config.big_blind, rng=self.rng)
        styles = opponent_styles(config, self.rng)
        self.styles = {seat: styles[seat - 1] for seat in range(1, config.opponents + 1)}
        self.strategies: dict[int, Strategy] = {
            seat: strategy_factory(style, config.difficulty, random.Random(self.rng.random()))
            for seat, style in self.styles.items()
        }
        self.slots = display_slots([s.seat for s in self.table.seats], HUMAN_SEAT)
        self.presenter = HandPresenter()
        self.hand_listeners: list[Callable[[HoldemHand], None]] = []
        # (seat, PlayerActed index, reason) for the current hand's opponent decisions.
        self._reasons: list[tuple[int, int, str]] = []

    # ---------------------------------------------------------------- state

    @property
    def hand(self) -> HoldemHand | None:
        return self.table.hand

    @property
    def caught_up(self) -> bool:
        """Has every engine event been presented?"""
        return self.hand is None or self.presenter.events_applied >= len(self.hand.events)

    @property
    def human_to_act(self) -> bool:
        hand = self.hand
        return hand is not None and not hand.is_complete and hand.to_act == HUMAN_SEAT and self.caught_up

    @property
    def opponent_to_act(self) -> int | None:
        hand = self.hand
        if hand is None or hand.is_complete or not self.caught_up or hand.to_act == HUMAN_SEAT:
            return None
        return hand.to_act

    @property
    def hand_over(self) -> bool:
        return self.hand is not None and self.hand.is_complete and self.caught_up

    @property
    def human_busted(self) -> bool:
        return self._final_stack(HUMAN_SEAT) == 0

    @property
    def opponents_busted(self) -> bool:
        return all(self._final_stack(seat) == 0 for seat in self.strategies)

    @property
    def session_over(self) -> bool:
        if self.hand is not None and not self.hand_over:
            return False
        return self.human_busted or self.opponents_busted

    @property
    def can_start_hand(self) -> bool:
        return (self.hand is None or self.hand_over) and not self.session_over

    def _final_stack(self, seat: int) -> int:
        hand = self.hand
        if hand is not None and hand.is_complete and seat in hand.result.final_stacks:
            return hand.result.final_stacks[seat]
        return self.table.seats[seat].stack

    # ---------------------------------------------------------------- flow

    def start_hand(self) -> HoldemHand:
        if not self.can_start_hand:
            raise SessionError("Cannot start a new hand now")
        hand = self.table.start_hand()
        self.presenter = HandPresenter()
        self._reasons = []
        if hand.is_complete:
            self._notify_complete(hand)
        return hand

    def next_event(self) -> HandEvent | None:
        """Present the next unpresented engine event, if any."""
        hand = self.hand
        if hand is None or self.caught_up:
            return None
        event = hand.events[self.presenter.events_applied]
        self.presenter.apply(event)
        return event

    def apply_human_action(self, kind: str, amount: int, step: int) -> None:
        if not self.human_to_act:
            raise SessionError("It is not your turn")
        self._act(HUMAN_SEAT, action_from_request(kind, amount), step)

    def play_opponent_action(self) -> PlayerActed:
        seat = self.opponent_to_act
        if seat is None:
            raise SessionError("No opponent is to act")
        hand = self.hand
        strategy = self.strategies[seat]
        action = strategy.decide(observe(hand, seat))
        event_index = len(hand.events)
        reason = getattr(strategy, "last_reason", "")
        try:
            self._act(seat, action, hand.action_count)
            if reason:
                self._reasons.append((seat, event_index, reason))
        except IllegalActionError:
            # A strategy must never stall the table: fall back to the safest legal action.
            log.error("Strategy for seat %s chose illegal %s; falling back", seat, action)
            legal = hand.legal_actions()
            self._act(seat, Action.check() if legal.can_check else Action.fold(), hand.action_count)
        return next(e for e in reversed(hand.events) if isinstance(e, PlayerActed))

    def _act(self, seat: int, action: Action, step: int) -> None:
        hand = self.hand
        hand.act(seat, action, expected_action_count=step)
        if hand.is_complete:
            self._notify_complete(hand)

    def _notify_complete(self, hand: HoldemHand) -> None:
        self.table.settle_hand()
        for listener in self.hand_listeners:
            listener(hand)

    # ---------------------------------------------------------------- view

    def roster(self) -> list[RosterSeat]:
        return [
            RosterSeat(s.seat, s.name, s.stack, "" if s.seat == HUMAN_SEAT else self.styles[s.seat].capitalize())
            for s in self.table.seats
        ]

    def build_view(self) -> TableView:
        hand = self.hand
        p = self.presenter
        to_act = hand.to_act if hand is not None and self.caught_up else None
        names = {s.seat: s.name for s in self.table.seats}
        return TableView(
            seats=seat_views(p, self.roster(), self.slots, HUMAN_SEAT, to_act),
            board=tuple(c.code for c in p.board),
            pots=pot_views(p, names),
            total_pot=p.total_pot(),
            street=p.street.value if p.street else "",
            hand_number=self.table.hand_number,
            small_blind=p.small_blind or self.table.small_blind,
            big_blind=p.big_blind or self.table.big_blind,
            message=self.message(),
            actions=self._human_actions(),
            hand_in_progress=hand is not None and not self.hand_over,
            session_active=True,
            can_deal=self.can_start_hand,
            session_over=self.session_over,
            winning_cards=winning_board_cards(p),
            analysis=self._analysis(),
        )

    def _analysis(self) -> tuple[AnalysisEntry, ...]:
        """Opponent reasoning with their hole cards, available only after the hand."""
        if not self.hand_over:
            return ()
        hand = self.hand
        entries = []
        for seat, index, reason in self._reasons:
            event = hand.events[index]
            entries.append(
                AnalysisEntry(
                    name=hand.player(seat).name,
                    street=event.street.value,
                    action=action_label(event),
                    reason=reason,
                    cards=tuple(c.code for c in hand.player(seat).hole),
                )
            )
        return tuple(entries)

    def _human_actions(self) -> ActionView | None:
        if not self.human_to_act:
            return None
        hand = self.hand
        legal = hand.legal_actions()
        return ActionView(
            step=hand.action_count,
            can_fold=legal.can_fold,
            can_check=legal.can_check,
            can_call=legal.can_call,
            call_amount=legal.call_amount,
            can_bet=legal.can_bet,
            can_raise=legal.can_raise,
            can_all_in=legal.can_all_in,
            min_to=legal.min_to,
            max_to=legal.max_to,
            stack=legal.stack,
            committed=legal.committed,
            presets=bet_presets(hand),
        )

    def message(self) -> str:
        hand = self.hand
        if hand is None:
            return "Press Deal to start the first hand"
        if self.hand_over:
            text = self.result_message()
            if self.human_busted:
                return text + " — you are out of chips"
            if self.opponents_busted:
                return text + " — you have won every chip at the table"
            return text
        if self.human_to_act:
            legal = hand.legal_actions()
            if legal.can_check:
                return "Your turn: check or bet" if legal.can_bet else "Your turn"
            return f"Your turn: {legal.call_amount:,} to call"
        if hand.to_act is not None and self.caught_up:
            return f"{hand.player(hand.to_act).name} is thinking…"
        return ""

    def result_message(self) -> str:
        return result_message(self.presenter)
