# Getting Started

teleflow turns annotated Python dataclasses into fully interactive Telegram bot interfaces. You declare *what* your bot collects — teleflow generates the handlers, keyboards, pagination, and session management.

## Installation

```bash
uv add teleflow --git https://github.com/prostomarkeloff/teleflow
```

Requires Python 3.14+. Depends on [emergent](https://github.com/prostomarkeloff/emergent) and [telegrinder](https://github.com/timoniq/telegrinder).

## Your first bot

Every teleflow app starts with a `TGApp` — a coordinator that owns all your patterns and ensures commands don't collide.

```python
from dataclasses import dataclass
from typing import Annotated

from kungfu import Ok, Result
from derivelib import derive
from derivelib._errors import DomainError
from teleflow.app import TGApp
from teleflow.flow import TextInput, Counter, FinishResult

# 1. Create the app
tg = TGApp(key_node=UserId)


# 2. Declare a flow
@derive(tg.flow("register", description="Sign up"))
@dataclass
class Registration:
    name: Annotated[str, TextInput("What's your name?")]
    age: Annotated[int, Counter("How old are you?", min=1, max=120)]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message(f"Welcome, {self.name}!"))
```

That's it. When a user sends `/register`, the bot walks them through two steps — a text prompt for `name` and a +/- counter for `age` — then calls `finish()`.

## Compiling to a Dispatch

teleflow patterns compile down to telegrinder `Dispatch` handlers through emergent's wire compiler:

```python
from emergent.wire.axis.surface._app import build_application_from_decorated
from telegrinder import API, Telegrinder

# Build the wire application from all @derive-decorated classes
app = build_application_from_decorated(Registration)

# Compile to telegrinder Dispatch
dp = tg.compile(app)

# Run the bot
bot = Telegrinder(API(token="BOT_TOKEN"), dispatch=dp)
bot.run_forever()
```

## Adding a browse view

Show your users a paginated list of entities:

```python
from teleflow.browse import BrowseSource, query, action, ActionResult

@derive(tg.browse("tasks", description="My tasks"))
@dataclass
class TaskCard:
    id: Annotated[int, Identity]
    title: str
    done: bool

    @classmethod
    @query
    async def fetch(cls, db: TaskDB) -> BrowseSource[TaskCard]:
        return ListBrowseSource(await db.all())

    @classmethod
    @action("Complete")
    async def complete(cls, entity: TaskCard, db: TaskDB) -> ActionResult:
        await db.mark_done(entity.id)
        return ActionResult.refresh("Done!")
```

`/tasks` shows a paginated card list with prev/next navigation and a "Complete" action button on each card.

## What's next

- [Flows & Widgets](flows.md) — all widget types, validation, dynamic options
- [Browse, Dashboard & Search](views.md) — entity views in depth
- [Settings](settings.md) — inline settings editing
- [Flow Transforms](transforms.md) — cancel, back, progress, sub-flows
- [Theming](theming.md) — customize every string and icon
