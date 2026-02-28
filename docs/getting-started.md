# Getting Started

teleflow turns Python dataclasses into Telegram bots. You annotate fields with widgets, and teleflow generates the handlers, keyboards, pagination, and session management. No manual callback routing, no state machines — just declare and derive.

## Install

```bash
uv add teleflow --git https://github.com/prostomarkeloff/teleflow
```

Requires Python 3.14+. Pulls in [emergent](https://github.com/prostomarkeloff/emergent) and [telegrinder](https://github.com/timoniq/telegrinder) automatically.

## Your first flow

The simplest thing you can build is a **flow** — a multi-step conversation. The bot asks questions one by one, collects answers into a typed dataclass, and calls your `finish()` method.

```python
from dataclasses import dataclass
from typing import Annotated

from kungfu import Ok, Result
from telegrinder.node import UserId
from derivelib import derive
from derivelib._errors import DomainError

from teleflow.app import TGApp
from teleflow.flow import TextInput, Counter, FinishResult

tg = TGApp(key_node=UserId)

@derive(tg.flow("greet", description="Say hello"))
@dataclass
class Greeting:
    name: Annotated[str, TextInput("What's your name?")]
    age: Annotated[int, Counter("How old are you?", min=1, max=120)]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message(f"Hello, {self.name}! {self.age} is a great age."))
```

When a user sends `/greet`, the bot sends "What's your name?" and waits. The user replies with text — that becomes `self.name`. Then the bot shows a `+`/`-` counter for age. After both fields are filled, `finish()` runs and sends back the message.

`TGApp` is the coordinator — it owns your patterns, ensures commands don't collide, and shares a theme and callback registry across everything.

## Adding a browse view

Flows collect data. **Browse** displays it. Here's a paginated list with action buttons:

```python
from emergent.wire.axis.schema import Identity
from teleflow.browse import ListBrowseSource, BrowseSource, ActionResult, query, action, format_card

@derive(tg.browse("items", page_size=3, description="View items"))
@dataclass
class ItemCard:
    id: Annotated[int, Identity]
    title: str
    done: bool

    @classmethod
    @query
    async def fetch(cls) -> BrowseSource[ItemCard]:
        return ListBrowseSource([
            ItemCard(1, "Write docs", False),
            ItemCard(2, "Ship v1", False),
        ])

    @classmethod
    @format_card
    def render(cls, item: ItemCard) -> str:
        icon = "done" if item.done else "todo"
        return f"[{icon}] {item.title}"

    @classmethod
    @action("Complete")
    async def complete(cls, item: ItemCard) -> ActionResult:
        return ActionResult.refresh(f"Completed: {item.title}")
```

`/items` shows the first page of cards with prev/next buttons and a "Complete" action on each card. The `id` field annotated with `Identity` tells teleflow which field uniquely identifies each entity.

## Compiling and running

teleflow patterns don't directly create handlers. They describe an **application** — a portable representation that gets compiled to a specific runtime. For Telegram, that runtime is telegrinder:

```python
from derivelib import build_application_from_decorated
from telegrinder import API, Telegrinder, Token
from emergent.wire.compile.targets import telegrinder as tg_compile

# Gather all @derive-decorated classes into a wire application
app = build_application_from_decorated(Greeting, ItemCard)

# Compile to telegrinder Dispatch
dp = tg_compile.compile(app)

# Run
bot = Telegrinder(API(Token("YOUR_BOT_TOKEN")), dispatch=dp)
bot.run_forever()
```

This two-step process (build application, then compile) is central to emergent's architecture. The application is target-agnostic — the same `@derive` declarations could compile to HTTP or CLI. For teleflow, the target is always telegrinder.

## What's next

You've seen the two core patterns — flows that collect data and browse views that display it. teleflow has three more patterns (dashboard, settings, search) and a rich widget library. Keep reading:

**Next: [Flows & Widgets](flows.md)** — the full widget catalog, validation, conditional fields, and custom widgets

---

[Docs index](readme.md)
