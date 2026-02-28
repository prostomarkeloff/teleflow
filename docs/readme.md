# teleflow docs

teleflow turns annotated Python dataclasses into complete Telegram bot interfaces — conversational wizards, paginated lists, settings panels, and more. You describe what the bot should do; teleflow handles keyboards, pagination, sessions, and state.

This guide walks you through the library concept by concept, building on each previous section. If you're new, start from the top.

## Reading order

1. **[Getting Started](getting-started.md)** — install, build your first bot, understand the compile loop
2. **[Flows & Widgets](flows.md)** — the core pattern: multi-step conversations and the 30+ widgets that power them
3. **[Views: Browse, Dashboard & Search](views.md)** — displaying and interacting with data
4. **[Settings](settings.md)** — user preferences with inline editing (reuses flow widgets)
5. **[Transforms](transforms.md)** — adding cancel, back, progress, sub-flows to any flow
6. **[Theming](theming.md)** — localizing every button label and icon

## Examples

Working bots you can run immediately:

- **[quickstart.py](../examples/quickstart.py)** — ~60 lines, one flow + one browse
- **[casino.py](../examples/casino.py)** — all five patterns in a single file

```bash
BOT_TOKEN=... uv run python examples/quickstart.py
```

## Russian

[Документация на русском](ru/readme.md)
