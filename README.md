# teleflow

Telegram UI patterns for [emergent](https://github.com/prostomarkeloff/emergent) + [derivelib](https://github.com/prostomarkeloff/emergent). Built on [telegrinder](https://github.com/timoniq/telegrinder).

Derive fully interactive Telegram interfaces from dataclass declarations.

[Документация на русском](docs/ru/readme.md)

## Patterns

- **flow** — multi-step conversational wizards with typed widgets (text input, inline buttons, counters, date pickers, etc.)
- **browse** — paginated entity lists with actions and filtering
- **dashboard** — single-entity interactive cards
- **settings** — settings overview with inline field editing
- **search** — search-first paginated browsing

## Usage

```python
from teleflow.app import TGApp
from teleflow.flow import TextInput, Counter
from derivelib import derive

tg = TGApp(key_node=UserId)

@derive(tg.flow("register", description="Sign up"))
@dataclass
class Registration:
    name: Annotated[str, TextInput("Your name?")]
    age: Annotated[int, Counter("Age:")]

@derive(tg.browse("tasks"))
@dataclass
class TaskCard:
    id: Annotated[int, Identity]
    title: str
```

## Install

```
uv add teleflow --git https://github.com/prostomarkeloff/teleflow
```

Requires Python 3.14+.

## Examples

- **[quickstart.py](examples/quickstart.py)** — minimal bot in ~60 lines: one flow (pizza order) + one browse (order list)
- **[casino.py](examples/casino.py)** — noir casino bot showcasing all patterns: dashboard (roulette), browse (missions), flow (cipher cracking), settings (player profile), methods (wallet/start)

```bash
BOT_TOKEN=... uv run python examples/quickstart.py
```

## Documentation

- [Getting Started](docs/getting-started.md)
- [Flows & Widgets](docs/flows.md)
- [Browse, Dashboard & Search](docs/views.md)
- [Settings](docs/settings.md)
- [Flow Transforms](docs/transforms.md)
- [Theming](docs/theming.md)
