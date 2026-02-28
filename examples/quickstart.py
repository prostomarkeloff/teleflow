"""quickstart — minimal teleflow bot in ~60 lines.

    BOT_TOKEN=... uv run python teleflow/examples/quickstart.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from kungfu import Ok, Result
from telegrinder.node import UserId

from emergent.wire.axis.schema import Identity
from derivelib import build_application_from_decorated, derive
from derivelib._errors import DomainError

from teleflow.app import TGApp
from teleflow.flow import TextInput, Counter, Inline, FinishResult, with_cancel, with_back
from teleflow.browse import ListBrowseSource, BrowseSource, ActionResult, query, action, format_card

tg = TGApp(key_node=UserId)

# ── Flow: collect a pizza order ──────────────────────────────────────────────

@derive(tg.flow("order", description="Order a pizza").chain(with_cancel(), with_back()))
@dataclass
class PizzaOrder:
    size: Annotated[str, Inline("Size:", small="Small", medium="Medium", large="Large")]
    toppings: Annotated[str, TextInput("Toppings (comma-separated):")]
    quantity: Annotated[int, Counter("How many?", min=1, max=10)]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message(
            f"Order placed!\n{self.quantity}x {self.size} pizza with {self.toppings}"))


# ── Browse: view placed orders ───────────────────────────────────────────────

orders: list[PizzaOrder] = []

@derive(tg.browse("orders", page_size=3, description="View orders"))
@dataclass
class OrderCard:
    id: Annotated[int, Identity]
    size: str
    toppings: str
    quantity: int

    @classmethod
    @query
    async def fetch(cls) -> BrowseSource[OrderCard]:
        return ListBrowseSource([
            OrderCard(i, o.size, o.toppings, o.quantity) for i, o in enumerate(orders)
        ])

    @classmethod
    @format_card
    def render(cls, c: OrderCard) -> str:
        return f"#{c.id} — {c.quantity}x {c.size} ({c.toppings})"

    @classmethod
    @action("Cancel")
    async def cancel(cls, c: OrderCard) -> ActionResult:
        return ActionResult.confirm(f"Cancel order #{c.id}?")


# ── Run ──────────────────────────────────────────────────────────────────────

app = build_application_from_decorated(PizzaOrder, OrderCard)

if __name__ == "__main__":
    import os
    from telegrinder import API, Telegrinder, Token
    from emergent.wire.compile.targets import telegrinder as tg_compile

    dp = tg_compile.compile(app)
    token = os.environ.get("BOT_TOKEN", "")
    if not token:
        print("Set BOT_TOKEN=... to run")
    else:
        bot = Telegrinder(API(Token(token)), dispatch=dp)
        bot.run_forever()
