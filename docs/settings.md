# Settings

`tg_settings()` generates a settings panel where users tap fields to edit them inline using flow widgets.

## Declaring settings

```python
from teleflow.settings import tg_settings, on_save, format_settings
from teleflow.flow import TextInput, Counter, Toggle

@derive(tg.settings("config", description="Bot settings"))
@dataclass
class BotConfig:
    nickname: Annotated[str, TextInput("New nickname:")]
    volume: Annotated[int, Counter("Volume:", min=0, max=100, step=10)]
    dark_mode: Annotated[bool, Toggle("Dark mode:")]

    @classmethod
    @query
    async def fetch(cls, uid: UserId, db: ConfigDB) -> BotConfig:
        return await db.get(uid.value)

    @classmethod
    @on_save
    async def save(cls, settings: BotConfig, uid: UserId, db: ConfigDB) -> None:
        await db.update(uid.value, settings)
```

When the user sends `/config`, they see an overview of current values with a button per field. Tapping a field opens the corresponding widget inline. After editing, `@on_save` persists the change.

## How it works

The settings pattern has two modes:

**Overview mode** — shows all fields as buttons:
```
Nickname: Alice
Volume: 70
Dark mode: On

[Nickname: Alice]  [Volume: 70]  [Dark mode: On]
```

**Editing mode** — renders the field's widget:
```
Volume:
   ← 70 →
[Done]  [Back]
```

Pressing Back returns to overview. Completing a widget edit triggers `@on_save` and returns to overview with the updated value.

## Decorators

### @query

Loads the current settings. Returns the settings dataclass instance (not a BrowseSource).

```python
@classmethod
@query
async def fetch(cls, uid: UserId, db: ConfigDB) -> BotConfig:
    return await db.get(uid.value)
```

### @on_save

Called after a field is edited. Receives the full settings object with the updated field.

```python
@classmethod
@on_save
async def save(cls, settings: BotConfig, uid: UserId, db: ConfigDB) -> None:
    await db.update(uid.value, settings)
```

### @format_settings

Optional custom renderer for the overview display.

```python
@classmethod
@format_settings
def render(cls, s: BotConfig) -> str:
    return f"Nickname: {s.nickname}\nVolume: {s.volume}%"
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `command` | `str` | required | Telegram command |
| `key_node` | `type` | required | nodnod session routing node |
| `*caps` | `SurfaceCapability` | `()` | Additional capabilities |
| `description` | `str \| None` | `None` | Help text |
| `order` | `int` | `100` | Sort order in help |
| `theme` | `UITheme` | default | UI customization |

## Widget reuse

Settings reuses the same widgets as flows. Any widget that works in a flow field annotation works in a settings field — TextInput, Counter, Toggle, Inline, Multiselect, DatePicker, etc.
