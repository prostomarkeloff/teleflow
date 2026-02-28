# Settings

Every bot has settings — language preference, notification toggles, default values. teleflow's settings pattern gives users an overview of their current choices and lets them edit any field inline, using the same widgets that power flows.

## How settings work

The settings pattern has two modes. **Overview mode** shows all fields as a summary with a button for each:

```
Nickname: Alice
Volume: 70
Dark mode: On

[Nickname: Alice]  [Volume: 70]  [Dark mode: On]
```

When the user taps a button, the view flips to **editing mode** — the field's widget renders inline (a text prompt, a counter, a toggle — whatever you annotated). After editing, `@on_save` fires, and the view returns to overview with the updated value.

## Declaring settings

```python
from teleflow.settings import tg_settings, on_save, format_settings
from teleflow.browse import query
from teleflow.flow import TextInput, Counter, Toggle

@derive(tg.settings("config", description="Bot settings"))
@dataclass
class BotConfig:
    nickname: Annotated[str, TextInput("New nickname:")]
    volume: Annotated[int, Counter("Volume:", min=0, max=100, step=10)]
    dark_mode: Annotated[bool, Toggle("Dark mode:")]

    @classmethod
    @query
    async def fetch(cls, uid: Annotated[int, compose.Node(UserId)],
                    db: ConfigDB) -> BotConfig:
        return await db.get(uid)

    @classmethod
    @on_save
    async def save(cls, settings: BotConfig, uid: Annotated[int, compose.Node(UserId)],
                   db: ConfigDB) -> None:
        await db.update(uid, settings)

    @classmethod
    @format_settings
    def render(cls, s: BotConfig) -> str:
        return f"Nickname: {s.nickname}\nVolume: {s.volume}%\nDark mode: {'On' if s.dark_mode else 'Off'}"
```

Three decorators, each with a clear role:

### @query — load current values

Returns the settings dataclass populated with current values. Just like in browse, it supports DI for accessing databases and the current user.

```python
@classmethod
@query
async def fetch(cls, uid: Annotated[int, compose.Node(UserId)]) -> BotConfig:
    ...
```

### @on_save — persist changes

Called every time the user edits a field. Receives the full settings object with the updated field already applied.

```python
@classmethod
@on_save
async def save(cls, settings: BotConfig, uid: Annotated[int, compose.Node(UserId)]) -> None:
    ...
```

### @format_settings — custom overview text

Optional. Controls what the user sees in overview mode. Without it, teleflow renders all fields as `field: value` lines.

```python
@classmethod
@format_settings
def render(cls, s: BotConfig) -> str:
    return f"Nickname: {s.nickname}\n..."
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `command` | `str` | required | Telegram command |
| `description` | `str \| None` | `None` | Help text |
| `order` | `int` | `100` | Sort position in help |

## Widget reuse

This is the key insight: settings reuses flow widgets. Annotate a field with `TextInput`, `Counter`, `Toggle`, `Inline`, `DatePicker` — any widget from [Flows & Widgets](flows.md) works. When the user taps a settings field, that widget renders as an inline editor. No separate widget system, no duplication.

---

**Prev: [Views](views.md)** | **Next: [Transforms](transforms.md)**

[Docs index](readme.md)
