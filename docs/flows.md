# Flows & Widgets

A flow is a conversation between your bot and a user. The bot asks questions, the user answers, and the answers accumulate into a typed dataclass. When every field is filled, your `finish()` method takes over.

## Declaring a flow

```python
from teleflow.flow import TextInput, Inline, FinishResult

@derive(tg.flow("order", description="Place an order"))
@dataclass
class Order:
    item: Annotated[str, Inline("Pick an item:", pizza="Pizza", burger="Burger")]
    note: Annotated[str, TextInput("Any special requests?")]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message(f"Ordered {self.item}!"))
```

Each field is annotated with a **widget** — the UI element the bot uses to collect that value. The flow walks through fields top to bottom, one at a time.

You can use `tg.flow(...)` through a `TGApp` (which shares key_node, theme, and validates uniqueness), or the standalone `tg_flow(command=..., key_node=...)` directly. `TGApp` is the recommended way.

### Flow parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `command` | `str` | required | Telegram command (`"order"` becomes `/order`) |
| `description` | `str \| None` | `None` | Help text shown in `/help` |
| `order` | `int` | `100` | Sort position in help listing |
| `show_mode` | `ShowMode` | `SEND` | How prompts render (see below) |
| `launch_mode` | `LaunchMode` | `STANDARD` | Re-entry behavior (see below) |

## Widgets

Widgets are the building blocks. Each one knows how to render itself (text + keyboard), handle user input, and validate the result.

### Collecting text

**TextInput(prompt)** is the most basic widget — the bot sends a prompt, the user replies with text:

```python
name: Annotated[str, TextInput("What's your name?")]
```

**NumberInput(prompt, min, max, shortcuts)** expects a number. You can add shortcut buttons for common values:

```python
amount: Annotated[int, NumberInput("How many?", min=1, max=100, shortcuts=(5, 10, 25))]
```

**PinInput(prompt, length, mask, secret)** shows a numpad for PIN entry. Digits appear masked:

```python
pin: Annotated[str, PinInput("Enter your PIN:", length=4, secret=True)]
```

### Choosing from options

When you need the user to pick from a predefined set:

**Inline(prompt, \*\*options)** shows buttons, one tap selects. Fast and stateless — best for short lists:

```python
color: Annotated[str, Inline("Pick color:", red="Red", blue="Blue", green="Green")]
```

**Radio(prompt, \*\*options)** is like Inline but shows selection state (a dot marks the current choice) and requires a "Done" tap to confirm. Better when users might reconsider:

```python
size: Annotated[str, Radio("T-shirt size:", s="S", m="M", l="L", xl="XL")]
```

**Multiselect(prompt, min_selected, max_selected, \*\*options)** lets users pick multiple items with checkmarks:

```python
toppings: Annotated[str, Multiselect(
    "Pick toppings:",
    cheese="Cheese", mushrooms="Mushrooms", peppers="Peppers",
    min_selected=1, max_selected=3,
)]
```

**ScrollingInline(prompt, page_size, \*\*options)** paginates large option sets so Telegram doesn't choke on huge keyboards:

```python
country: Annotated[str, ScrollingInline("Country:", page_size=8, **country_map)]
```

**EnumInline(prompt)** auto-generates options from a Python Enum — no need to repeat labels:

```python
class Priority(enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

priority: Annotated[Priority, EnumInline("Priority:")]
```

All selection widgets accept `columns: int` to control how many buttons appear per row (default 1).

### Yes/no and toggles

**Confirm(prompt)** is a Yes/No question that resolves to `bool`:

```python
agree: Annotated[bool, Confirm("Accept terms?")]
```

**Toggle(prompt)** is a one-tap boolean flip — shows the current state and switches on press:

```python
notifications: Annotated[bool, Toggle("Notifications:")]
```

### Numbers and ranges

**Counter(prompt, min, max, step, default)** shows `+`/`-` buttons for stepping through integers:

```python
quantity: Annotated[int, Counter("How many?", min=1, max=99, step=1, default=1)]
```

**Slider(prompt, min, max, step, big_step, default, presets, bar_width, filled, empty)** renders a visual progress bar with fine and coarse controls:

```python
volume: Annotated[int, Slider("Volume:", min=0, max=100, step=5, big_step=20)]
```

**Rating(prompt, max_stars, filled, empty)** shows a star row for ratings:

```python
score: Annotated[int, Rating("Rate us:", max_stars=5)]
```

### Dates and times

**DatePicker(prompt, min_date, max_date)** renders a full calendar with month/year navigation:

```python
from datetime import date
birthday: Annotated[str, DatePicker("Birthday:", max_date=date.today())]
```

**TimePicker(prompt, min_hour, max_hour, step_minutes)** is a two-step picker — choose the hour, then the minute:

```python
alarm: Annotated[str, TimePicker("Alarm time:", min_hour=6, max_hour=22, step_minutes=15)]
```

**RecurrencePicker(prompt)** combines weekday selection with a time picker. Returns a string like `"0,2,4@10:30"` (Mon/Wed/Fri at 10:30):

```python
schedule: Annotated[str, RecurrencePicker("Recurring schedule:")]
```

**TimeSlotPicker(prompt, columns, date_format)** shows date-grouped time slots loaded dynamically via `@options` (see dynamic options below):

```python
slot: Annotated[str, TimeSlotPicker("Pick a slot:")]
```

### Media uploads

Media widgets collect Telegram `file_id` strings (except `LocationInput` which collects coordinates):

```python
photo: Annotated[str, PhotoInput("Send a photo:")]
doc: Annotated[str, DocumentInput("Upload a document:")]
video: Annotated[str, VideoInput("Send a video:")]
voice: Annotated[str, VoiceInput("Record a voice message:")]
location: Annotated[str, LocationInput("Share your location:")]
contact: Annotated[str, ContactInput("Share your contact:")]
```

**MediaGroupInput(prompt, min, max, accept)** collects multiple media files:

```python
photos: Annotated[str, MediaGroupInput("Send photos:", min=1, max=5, accept="photo")]
```

### Lists

**ListBuilder(prompt, min, max)** collects a variable-length list of text items. The user sends items one by one and presses Done when finished:

```python
tags: Annotated[str, ListBuilder("Add tags (send one at a time):", min=1, max=10)]
```

## Dynamic options

Sometimes you don't know the options ahead of time — they come from a database or an API. Use `@options("field_name")` to load them at runtime:

```python
from teleflow.widget import options

@derive(tg.flow("assign", description="Assign task"))
@dataclass
class AssignTask:
    assignee: Annotated[str, DynamicInline("Assign to:")]

    @classmethod
    @options("assignee")
    async def load_users(cls, db: UserDB) -> dict[str, str]:
        users = await db.all()
        return {str(u.id): u.name for u in users}
```

The options method returns `dict[str, str]` — keys are stored values, values are display labels. It can accept DI dependencies just like any other method.

Dynamic widget variants: `DynamicInline`, `DynamicRadio`, `DynamicMultiselect`, `TimeSlotPicker`.

## Conditional fields

Not every field is relevant for every user. `When()` makes a field conditional — it's only prompted when the predicate returns True:

```python
from teleflow.flow import When

kind: Annotated[str, Inline("Type:", bug="Bug", feature="Feature")]
severity: Annotated[str, Inline("Severity:", high="High", low="Low"),
    When(lambda state: state.get("kind") == "bug")]
```

The predicate receives a `dict[str, object]` of all field values collected so far. If `kind` isn't `"bug"`, `severity` is silently skipped.

## Validation

Stack validation annotations alongside widgets — they're checked automatically on every input:

```python
from teleflow.flow import MinLen, MaxLen, Pattern

username: Annotated[str, TextInput("Username:"), MinLen(3), MaxLen(20)]
email: Annotated[str, TextInput("Email:"), Pattern(r"^[\w.]+@[\w.]+$")]
```

On failure, the user sees an error (customizable via theming) and is re-prompted for the same field.

## Finishing a flow

Every flow needs a `finish()` method. It runs once all fields are collected:

```python
async def finish(self) -> Result[FinishResult, DomainError]:
    return Ok(FinishResult.message("Done!"))
```

`FinishResult` has several constructors for different outcomes:

- **`FinishResult.message(text)`** — send a text reply and end
- **`FinishResult.then(text, command="next")`** — reply, then redirect to another command
- **`FinishResult.sub_flow(text, command="child")`** — push current flow to stack and launch a sub-flow (requires `with_stacking`, see [Transforms](transforms.md))
- **`FinishResult.with_keyboard(text, markup)`** — reply with a custom inline or reply keyboard

`finish()` can also accept DI dependencies through `compose.Node` annotations — access databases, services, or the current user just like `@query` methods.

## ShowMode and LaunchMode

Two enums control how the flow presents itself:

**ShowMode** — how each prompt appears in the chat:

| Mode | What happens |
|------|-------------|
| `ShowMode.SEND` | A new message for each prompt (default). Simple and reliable. |
| `ShowMode.EDIT` | Edits the previous message in place. Keeps the chat clean. |
| `ShowMode.DELETE_AND_SEND` | Deletes the old message, sends a new one. Useful when switching between text and media prompts. |

**LaunchMode** — what happens when a user sends the command while a flow is already active:

| Mode | What happens |
|------|-------------|
| `LaunchMode.STANDARD` | The command text is treated as input for the current field (default). |
| `LaunchMode.RESET` | Resets the flow and starts from scratch. |
| `LaunchMode.EXCLUSIVE` | Blocks with an "already in progress" message. |
| `LaunchMode.SINGLE_TOP` | Re-sends the current prompt — continues where they left off. |

Set them on the flow or override with transforms:

```python
@derive(tg.flow("quiz", show_mode=ShowMode.EDIT, launch_mode=LaunchMode.EXCLUSIVE))
```

## Special widgets

**Prefilled()** — a field that's filled from context, never prompted to the user:

```python
user_id: Annotated[int, Prefilled()]
```

**Case(selector, \*\*options)** — shows different prompt text depending on a previous field's value:

```python
kind: Annotated[str, Inline("Type:", bug="Bug", feature="Feature")]
details: Annotated[str, Case(selector="kind", bug="Describe the bug:", feature="Describe the feature:")]
```

**SummaryReview(\*\*labels)** — displays all collected values for the user to review before confirming:

```python
confirm: Annotated[bool, SummaryReview(name="Name", age="Age")]
```

**Either(primary, secondary)** — tries the primary widget first, falls back to the secondary:

```python
input: Annotated[str, Either(PhotoInput("Send a photo:"), TextInput("Or type a description:"))]
```

## Custom widgets

If the built-in widgets don't fit, implement the `FlowWidget` protocol:

```python
from teleflow.widget import WidgetContext, Advance, Reject, NoOp

class ColorPicker:
    @property
    def prompt(self) -> str:
        return "Pick a color:"

    @property
    def needs_callback(self) -> bool:
        return True  # this widget uses inline keyboard

    async def render(self, ctx: WidgetContext) -> tuple[str, AnyKeyboard | None]:
        # build and return (text, keyboard)
        ...

    async def handle_callback(self, value: str, ctx: WidgetContext) -> Advance | Reject | NoOp:
        return Advance(value=value, summary=value)

    async def handle_message(self, message: MessageCute, ctx: WidgetContext) -> Advance | Reject | NoOp:
        return Reject(message="Please use the buttons above.")
```

Widget handlers return one of four result types:

| Type | What happens |
|------|-------------|
| `Advance(value, summary)` | Store the value, move to the next field |
| `Stay(new_value)` | Re-render the widget with updated state (e.g., counter increment) |
| `Reject(message)` | Show an error, stay on the current field |
| `NoOp()` | Do nothing |

`WidgetContext` gives you access to `flow_name`, `field_name`, `current_value`, `base_type`, `validators`, `is_optional`, `flow_state` (collected values so far), `dynamic_options`, and `theme`.

---

**Prev: [Getting Started](getting-started.md)** | **Next: [Views](views.md)**

[Docs index](readme.md)
