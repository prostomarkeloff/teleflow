# Flows & Widgets

A flow is a multi-step conversation. The user sends `/command`, the bot asks questions one by one, collects answers into a typed dataclass, and calls `finish()`.

## Declaring a flow

```python
from teleflow.flow import tg_flow, TextInput, Inline

@derive(tg_flow(
    command="order",
    key_node=UserId,
    description="Place an order",
))
@dataclass
class Order:
    item: Annotated[str, Inline("Pick an item:", pizza="Pizza", burger="Burger")]
    note: Annotated[str, TextInput("Any special requests?")]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message(f"Ordered {self.item}!"))
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `command` | `str` | required | Telegram command name (`"start"` → `/start`) |
| `key_node` | `type` | required | nodnod node for session routing (e.g. `UserId`) |
| `*caps` | `SurfaceCapability` | `()` | Additional surface capabilities |
| `description` | `str \| None` | `None` | Help text for `/help` |
| `order` | `int` | `100` | Sort order in help listing |
| `show_mode` | `ShowMode` | `SEND` | How prompts render |
| `launch_mode` | `LaunchMode` | `STANDARD` | Re-entry behavior |
| `theme` | `UITheme` | default | UI strings and icons |

When using `TGApp`, prefer `tg.flow(...)` over `tg_flow(...)` directly — it shares the app's key_node, theme, and validates command uniqueness.

## Widgets

Each dataclass field is annotated with a widget that controls how the bot collects that value.

### Basic input

**TextInput(prompt)** — Collect a text message.

```python
name: Annotated[str, TextInput("What's your name?")]
```

**NumberInput(prompt, min, max, shortcuts)** — Collect a number. Optional quick-select buttons.

```python
amount: Annotated[int, NumberInput("How many?", min=1, max=100, shortcuts=(5, 10, 25))]
```

**Confirm(prompt, yes_label, no_label)** — Yes/No question. Resolves to `bool`.

```python
agree: Annotated[bool, Confirm("Accept terms?")]
```

### Selection

**Inline(prompt, columns, \*\*options)** — Single-select inline keyboard. Fast, no persistent state.

```python
color: Annotated[str, Inline("Pick color:", red="Red", blue="Blue", green="Green")]
```

**Radio(prompt, columns, \*\*options)** — Single-select with visible selection state and a Done button.

```python
size: Annotated[str, Radio("T-shirt size:", s="S", m="M", l="L", xl="XL")]
```

**Multiselect(prompt, columns, min_selected, max_selected, \*\*options)** — Multi-select with checkmarks.

```python
toppings: Annotated[str, Multiselect(
    "Pick toppings:",
    cheese="Cheese", mushrooms="Mushrooms", peppers="Peppers",
    min_selected=1, max_selected=3,
)]
```

**ScrollingInline(prompt, columns, page_size, \*\*options)** — Paginated inline for large option sets.

```python
country: Annotated[str, ScrollingInline("Country:", page_size=8, **country_map)]
```

**EnumInline(prompt, columns)** — Auto-generates options from a Python Enum.

```python
class Priority(enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

priority: Annotated[Priority, EnumInline("Priority:")]
```

### Interactive

**Counter(prompt, min, max, step, default)** — +/- stepper for integers.

```python
quantity: Annotated[int, Counter("How many?", min=1, max=99, step=1, default=1)]
```

**Toggle(prompt, on, off)** — One-tap boolean flip.

```python
notifications: Annotated[bool, Toggle("Notifications:", on="On", off="Off")]
```

**Slider(prompt, min, max, step, big_step, default, presets, filled, empty)** — Visual slider with progress bar.

```python
volume: Annotated[int, Slider("Volume:", min=0, max=100, step=5, big_step=20)]
```

**Rating(prompt, max_stars, filled, empty)** — Star rating.

```python
score: Annotated[int, Rating("Rate us:", max_stars=5)]
```

**ListBuilder(prompt, min, max)** — Collect a list of text items one by one.

```python
tags: Annotated[str, ListBuilder("Add tags (send one at a time):", min=1, max=10)]
```

**PinInput(prompt, length, mask, secret)** — Numpad PIN entry.

```python
pin: Annotated[str, PinInput("Enter PIN:", length=4, secret=True)]
```

### Date & time

**DatePicker(prompt, min_date, max_date)** — Calendar with month/year navigation.

```python
from datetime import date
birthday: Annotated[str, DatePicker("Birthday:", max_date=date.today())]
```

**TimePicker(prompt, min_hour, max_hour, step_minutes)** — Hour + minute selection.

```python
alarm: Annotated[str, TimePicker("Alarm time:", min_hour=6, max_hour=22, step_minutes=15)]
```

**TimeSlotPicker(prompt, columns, date_format)** — Date-grouped time slots from `@options`.

```python
slot: Annotated[str, TimeSlotPicker("Pick a slot:")]

@classmethod
@options("slot")
async def available_slots(cls) -> dict[str, str]:
    return {"2024-03-15T10:00": "Mar 15, 10:00", ...}
```

**RecurrencePicker(prompt, min_hour, max_hour, step_minutes)** — Weekday + time picker. Returns `"0,2,4@10:30"`.

```python
schedule: Annotated[str, RecurrencePicker("Recurring schedule:")]
```

### Media

All media widgets collect a `file_id` string (except LocationInput which collects a `(lat, lon)` tuple).

```python
photo: Annotated[str, PhotoInput("Send a photo:")]
doc: Annotated[str, DocumentInput("Upload a document:")]
video: Annotated[str, VideoInput("Send a video:")]
voice: Annotated[str, VoiceInput("Record a voice message:")]
location: Annotated[str, LocationInput("Share your location:")]
contact: Annotated[str, ContactInput("Share your contact:", button_text="Send contact")]
```

**MediaGroupInput(prompt, min, max, accept)** — Collect multiple media files.

```python
photos: Annotated[str, MediaGroupInput("Send photos:", min=1, max=5, accept="photo")]
```

### Conditional & review

**Prefilled()** — Pre-filled from context, not prompted.

```python
user_id: Annotated[int, Prefilled()]
```

**Case(selector, \*\*options)** — Display different text based on a previous field's value.

```python
kind: Annotated[str, Inline("Type:", bug="Bug", feature="Feature")]
details: Annotated[str, Case(
    selector="kind",
    bug="Describe the bug:",
    feature="Describe the feature:",
)]
```

**SummaryReview(\*\*labels)** — Show all collected values for confirmation before finishing.

```python
confirm: Annotated[bool, SummaryReview(name="Name", age="Age")]
```

### Dynamic options

Use `@options("field_name")` to load options at runtime:

```python
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

Dynamic widget variants: `DynamicInline`, `DynamicRadio`, `DynamicMultiselect`.

The options provider can accept compose.Node dependencies (injected via DI) and can reference previously collected field values by parameter name.

## Finishing a flow

Every flow entity must have a `finish()` method:

```python
async def finish(self) -> Result[FinishResult, DomainError]:
    ...
```

`FinishResult` controls what happens after the flow completes:

```python
# Simple text response
FinishResult.message("Done!")

# Text + redirect to another command
FinishResult.then("Created!", command="tasks")

# Push to stack + start sub-flow
FinishResult.sub_flow("Starting invite flow...", command="invite")

# Text with inline keyboard
FinishResult.with_keyboard("Choose next:", markup)
```

## Validation

Add validation annotations alongside widgets:

```python
from teleflow.flow import MinLen, MaxLen, Pattern

username: Annotated[str, TextInput("Username:"), MinLen(3), MaxLen(20)]
email: Annotated[str, TextInput("Email:"), Pattern(r"^[\w.]+@[\w.]+$")]
```

Validation runs automatically. On failure, the user sees an error message and is re-prompted.

## Conditional fields

Use `When()` to conditionally show fields:

```python
from teleflow.flow import When

kind: Annotated[str, Inline("Type:", bug="Bug", feature="Feature")]
severity: Annotated[str, Inline("Severity:", high="High", low="Low"),
    When(lambda v: v.get("kind") == "bug")]
```

`severity` is only prompted when `kind == "bug"`. Otherwise it's skipped entirely.

## ShowMode

Controls how prompts appear in the chat:

| Mode | Behavior |
|------|----------|
| `ShowMode.SEND` | Send a new message for each prompt (default) |
| `ShowMode.EDIT` | Edit the previous message in place (clean chat) |
| `ShowMode.DELETE_AND_SEND` | Delete old message + send new (for media type changes) |

## LaunchMode

Controls what happens when a user re-enters a flow that's already active:

| Mode | Behavior |
|------|----------|
| `LaunchMode.STANDARD` | Command text is treated as field input (continue flow) |
| `LaunchMode.RESET` | Reset and start the flow from scratch |
| `LaunchMode.EXCLUSIVE` | Block with "already in progress" message |
| `LaunchMode.SINGLE_TOP` | Re-send current prompt, continue where left off |

## Custom widgets

Implement the `FlowWidget` protocol to create your own widget:

```python
from teleflow.widget import FlowWidget, WidgetContext, Stay, Advance, Reject, NoOp

class ColorPicker:
    def __init__(self, prompt: str):
        self._prompt = prompt

    @property
    def prompt(self) -> str:
        return self._prompt

    @property
    def needs_callback(self) -> bool:
        return True  # True if using inline keyboard

    async def render(self, ctx: WidgetContext) -> tuple[str, AnyKeyboard | None]:
        kb = InlineKeyboard()
        # ... build keyboard
        return self._prompt, kb

    async def handle_callback(self, value: str, ctx: WidgetContext) -> Advance | Stay | Reject | NoOp:
        return Advance(value=value, summary=value)

    async def handle_message(self, message: MessageCute, ctx: WidgetContext) -> Advance | Stay | Reject | NoOp:
        return Reject(message="Please use the buttons above.")
```

Result types:

| Type | Meaning |
|------|---------|
| `Advance(value, summary)` | Store value, move to next field |
| `Stay(new_value)` | Re-render widget (e.g. counter increment) |
| `Reject(message)` | Show error, stay on current field |
| `NoOp()` | Do nothing |
