"""casino — noir casino bot. All patterns in one file.

    /roulette   — spin the wheel          (dashboard + actions + tabs)
    /missions   — spy mission board        (browse + tabs + format_card)
    /cipher     — crack a code             (flow + custom widget)
    /settings   — player settings          (settings + on_save)
    /wallet     — check chips              (methods + tg_command)
    /help       — command reference        (methods + tg_command)

    BOT_TOKEN=... uv run python teleflow/examples/casino.py
"""

from __future__ import annotations

import hashlib
import random
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Annotated, ClassVar

from kungfu import Ok, Result, Some
from nodnod import scalar_node  # type: ignore[import-untyped]
from telegrinder.node import UserId

from emergent.wire.axis.schema import Identity
from emergent.wire.axis.schema.dialects import compose, tg
from derivelib import build_application_from_decorated, derive, endpoint_count
from derivelib._errors import DomainError
from derivelib.patterns import methods

from teleflow.methods import tg_command
from teleflow.flow import (
    tg_flow, TextInput, Confirm, Counter, Inline, ShowMode,
    FinishResult, with_cancel, with_show_mode,
)
from teleflow.widget import WidgetContext, Stay, Advance, Reject, NoOp
from teleflow.browse import (
    tg_browse, BrowseSource, ListBrowseSource, ActionResult,
    query, action, format_card, view_filter,
)
from teleflow.dashboard import tg_dashboard
from teleflow.settings import tg_settings, on_save, format_settings


# ── Domain ───────────────────────────────────────────────────────────────────

@dataclass
class Player:
    chips: int = 1000
    codename: str = "Rookie"
    missions_done: int = 0


@dataclass(frozen=True, slots=True)
class Mission:
    id: Annotated[int, Identity]
    name: Annotated[str, tg.Bold()]
    difficulty: str
    reward: int
    description: str


MISSIONS: tuple[Mission, ...] = (
    Mission(1, "Dead Drop Pickup", "easy", 50, "Retrieve a package from the old café."),
    Mission(2, "Safe Cracker", "medium", 200, "Open the vault in the east wing."),
    Mission(3, "Train Intercept", "hard", 700, "Board the Orient Express. Find the briefcase."),
    Mission(4, "Embassy Tail", "easy", 50, "Follow the attaché. Don't be seen."),
    Mission(5, "Double Cross", "medium", 200, "Turn the informant. Make it convincing."),
    Mission(6, "Rooftop Extraction", "hard", 700, "Helicopter at midnight. Don't miss it."),
)

CIPHER_WORDS = ("NIGHTFALL", "SCARLET", "VENOM", "SHADOW", "MERCURY", "PHANTOM")

ROULETTE_REDS = frozenset({1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36})


# ── State (injected via nodnod) ──────────────────────────────────────────────

@dataclass
class Casino:
    players: dict[int, Player] = field(default_factory=dict)

    def player(self, uid: int) -> Player:
        return self.players.setdefault(uid, Player())


casino = Casino()


@scalar_node
class CasinoNode:
    @classmethod
    def __compose__(cls) -> Casino:
        return casino


# ── /roulette — dashboard with bet tabs and color actions ────────────────────

async def _spin(bet: int, choice: str, uid: int, c: Casino) -> ActionResult:
    p = c.player(uid)
    if p.chips < bet:
        return ActionResult.stay(f"Not enough chips! ({p.chips})")
    p.chips -= bet
    winning = random.randint(0, 36)
    won = (
        (choice == "red" and winning in ROULETTE_REDS) or
        (choice == "black" and winning != 0 and winning not in ROULETTE_REDS) or
        (choice == "green" and winning == 0)
    )
    payout = (bet * 35 if choice == "green" else bet * 2) if won else 0
    p.chips += payout
    msg = f"Ball: {winning}. {'Won ' + str(payout) if won else 'Lost ' + str(bet)} chips."
    return ActionResult.refresh(msg)


@derive(tg_dashboard(command="roulette", key_node=UserId, description="Spin the wheel", order=2))
@dataclass
class RouletteTable:
    id: Annotated[int, Identity] = 0
    bet: int = 50
    balance: int = 1000

    @classmethod
    @view_filter("250", key="250")
    @view_filter("100", key="100")
    @view_filter("50", key="50")
    @query
    async def table(
        cls,
        uid: Annotated[int, compose.Node(UserId)],
        c: Annotated[Casino, compose.Node(CasinoNode)],
        filter_key: str = "",
    ) -> RouletteTable:
        bet = int(filter_key) if filter_key.isdigit() else 50
        return RouletteTable(id=1, bet=bet, balance=c.player(uid).chips)

    @classmethod
    @format_card
    def render_table(cls, t: RouletteTable) -> str:
        return f"🎰 Roulette\n💰 Bet: {t.bet}\n💵 Balance: {t.balance}"

    @classmethod
    @action("🔴 Red", row=0)
    async def red(cls, t: RouletteTable, uid: Annotated[int, compose.Node(UserId)],
                  c: Annotated[Casino, compose.Node(CasinoNode)]) -> ActionResult:
        return await _spin(t.bet, "red", uid, c)

    @classmethod
    @action("⚫ Black", row=0)
    async def black(cls, t: RouletteTable, uid: Annotated[int, compose.Node(UserId)],
                    c: Annotated[Casino, compose.Node(CasinoNode)]) -> ActionResult:
        return await _spin(t.bet, "black", uid, c)

    @classmethod
    @action("🟢 Green", row=0)
    async def green(cls, t: RouletteTable, uid: Annotated[int, compose.Node(UserId)],
                    c: Annotated[Casino, compose.Node(CasinoNode)]) -> ActionResult:
        return await _spin(t.bet, "green", uid, c)


# ── /missions — browse spy missions with difficulty tabs ─────────────────────

@derive(tg_browse(command="missions", key_node=UserId, page_size=3,
                  description="Spy mission board", order=3))
@dataclass
class MissionBoard:
    id: Annotated[int, Identity] = 0

    @classmethod
    @view_filter("Hard", key="hard")
    @view_filter("Medium", key="medium")
    @view_filter("Easy", key="easy")
    @query
    async def missions(cls, filter_key: str = "") -> BrowseSource[Mission]:
        filtered = [m for m in MISSIONS if m.difficulty == filter_key] if filter_key else list(MISSIONS)
        return ListBrowseSource(filtered)

    @classmethod
    @format_card
    def render(cls, m: Mission) -> str:
        icon = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(m.difficulty, "⚪")
        return f"{icon} <b>{m.name}</b>\n{m.description}\nReward: {m.reward} chips"

    @classmethod
    @action("🕵️ Accept")
    async def accept(cls, mission: Mission, uid: Annotated[int, compose.Node(UserId)],
                     c: Annotated[Casino, compose.Node(CasinoNode)]) -> ActionResult:
        odds = {"easy": 0.8, "medium": 0.55, "hard": 0.3}
        p = c.player(uid)
        if random.random() < odds.get(mission.difficulty, 0.5):
            p.chips += mission.reward
            p.missions_done += 1
            return ActionResult.stay(f"✅ Mission complete! +{mission.reward} chips")
        return ActionResult.stay("❌ Mission failed. No reward.")


# ── /cipher — crack the code (flow + custom widget) ──────────────────────────

def _current_cipher() -> str:
    return CIPHER_WORDS[int(time.time() // 600) % len(CIPHER_WORDS)]


class CipherInput:
    """Dynamic-prompt widget that regenerates the puzzle each render."""

    @property
    def prompt(self) -> str:
        word = _current_cipher()
        h = hashlib.md5(word.encode()).hexdigest()[:6]  # noqa: S324
        return f"🔐 Intercept #{h.upper()} — {len(word)} letters, starts with '{word[0]}'\n\nEnter the code word:"

    @property
    def needs_callback(self) -> bool:
        return False

    async def render(self, ctx: WidgetContext) -> tuple[str, None]:
        return self.prompt, None

    async def handle_message(self, message: object, ctx: WidgetContext) -> Advance | Reject:
        text = getattr(getattr(message, "text", None), "value", None)
        if text:
            return Advance(value=text.strip(), summary=text.strip()[:20])
        return Reject(message="Send a text message.")

    async def handle_callback(self, value: str, ctx: WidgetContext) -> NoOp:
        return NoOp()


@derive(tg_flow(command="cipher", key_node=UserId, description="Crack the code", order=4).chain(
    with_cancel(), with_show_mode(ShowMode.EDIT),
))
@dataclass
class CipherChallenge:
    answer: Annotated[str, CipherInput()] = ""

    async def finish(
        self, uid: Annotated[int, compose.Node(UserId)],
        c: Annotated[Casino, compose.Node(CasinoNode)],
    ) -> Result[FinishResult, DomainError]:
        secret = _current_cipher()
        p = c.player(uid)
        if self.answer.upper().strip() == secret:
            p.chips += 200
            return Ok(FinishResult.message(f"🔓 Correct! Code: {secret}\n+200 chips (balance: {p.chips})"))
        hint = secret[:len(self.answer) // 2 + 1] + "·" * (len(secret) - len(self.answer) // 2 - 1)
        return Ok(FinishResult.message(f"❌ Wrong. Hint: {hint}\nTry /cipher again!"))


# ── /settings — player settings ──────────────────────────────────────────────

@derive(tg_settings(command="settings", key_node=UserId, description="Player settings", order=5))
@dataclass
class PlayerSettings:
    codename: Annotated[str, TextInput("Enter codename:")]
    notifications: Annotated[bool, Confirm("Enable notifications?")]
    default_bet: Annotated[int, Counter("Default bet:", min=10, max=500, step=10, default=50)]

    @classmethod
    @query
    async def load(cls, uid: Annotated[int, compose.Node(UserId)],
                   c: Annotated[Casino, compose.Node(CasinoNode)]) -> PlayerSettings:
        p = c.player(uid)
        return PlayerSettings(codename=p.codename, notifications=True, default_bet=50)

    @classmethod
    @on_save
    async def save(cls, s: PlayerSettings, uid: Annotated[int, compose.Node(UserId)],
                   c: Annotated[Casino, compose.Node(CasinoNode)]) -> None:
        c.player(uid).codename = s.codename

    @classmethod
    @format_settings
    def render(cls, s: PlayerSettings) -> str:
        return f"Codename: {s.codename}\nNotifications: {'On' if s.notifications else 'Off'}\nDefault bet: {s.default_bet}"


# ── Instant commands ─────────────────────────────────────────────────────────

@derive(methods)
@dataclass
class CasinoMenu:
    id: Annotated[int, Identity] = 0

    @classmethod
    @tg_command("start", description="Welcome", order=1)
    async def start(cls) -> Result[str, DomainError]:
        return Ok(
            "🎰 <b>Casino Royale</b>\n\n"
            "/roulette — spin the wheel\n"
            "/missions — spy missions\n"
            "/cipher — crack codes\n"
            "/wallet — your chips\n"
            "/settings — player settings")

    @classmethod
    @tg_command("wallet", description="Check chips", order=6)
    async def wallet(cls, uid: Annotated[int, compose.Node(UserId)],
                     c: Annotated[Casino, compose.Node(CasinoNode)]) -> Result[str, DomainError]:
        p = c.player(uid)
        return Ok(f"💰 <b>Wallet</b>\n\nChips: {p.chips}\nCodename: {p.codename}\nMissions: {p.missions_done}")


# ── Run ──────────────────────────────────────────────────────────────────────

app = build_application_from_decorated(
    CasinoMenu, RouletteTable, MissionBoard, CipherChallenge, PlayerSettings,
)

if __name__ == "__main__":
    import os
    from telegrinder import API, Telegrinder, Token
    from emergent.wire.compile.targets import telegrinder as tg_compile

    dp = tg_compile.compile(app)
    n = endpoint_count(app)
    print(f"\n  🎰 Casino Royale — {n} endpoints from 5 entities\n")
    token = os.environ.get("BOT_TOKEN", "")
    if not token:
        print("  Set BOT_TOKEN=... to run\n")
    else:
        bot = Telegrinder(API(Token(token)), dispatch=dp)
        bot.run_forever()
