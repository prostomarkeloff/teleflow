# Views: Browse, Dashboard & Search

Flows collect data from users. Views show data back to them. teleflow has three view patterns — each one answers a different question.

**Browse**: "Here's a list of things. Page through them, do stuff." \
**Dashboard**: "Here's one thing. Look at it, do stuff." \
**Search**: "What are you looking for?" Then browse the results.

All three share the same decorators (`@query`, `@action`, `@format_card`, `@view_filter`) and the same `ActionResult` system. Once you learn one, the others are variations.

## Browse

The workhorse. Takes an entity class and compiles it into paginated cards with navigation and action buttons.

```python
from emergent.wire.axis.schema import Identity
from teleflow.browse import ListBrowseSource, BrowseSource, ActionResult, query, action, format_card

@derive(tg.browse("tasks", page_size=5, description="My tasks"))
@dataclass
class TaskCard:
    id: Annotated[int, Identity]
    title: str
    status: str

    @classmethod
    @query
    async def fetch(cls, db: TaskDB) -> BrowseSource[TaskCard]:
        return ListBrowseSource(await db.all())

    @classmethod
    @format_card
    def render(cls, task: TaskCard) -> str:
        icon = "done" if task.status == "done" else "open"
        return f"[{icon}] <b>{task.title}</b>"

    @classmethod
    @action("Complete", row=0)
    async def complete(cls, task: TaskCard, db: TaskDB) -> ActionResult:
        await db.mark_done(task.id)
        return ActionResult.refresh("Marked as done!")
```

The user sends `/tasks` and sees page 1 with prev/next buttons. Each card shows the formatted text and action buttons below.

### Browse parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `command` | `str` | required | Telegram command |
| `page_size` | `int` | `5` | Items per page |
| `empty_text` | `str` | `"Nothing found."` | Shown when there's no data |
| `description` | `str \| None` | `None` | Help text |
| `order` | `int` | `100` | Sort position in help |
| `cb_prefix` | `str` | `""` | Custom callback prefix (auto-generated if empty) |

### @query — where the data comes from

The `@query` classmethod is the data source. It must return a `BrowseSource[T]` — a protocol with two methods:

```python
class BrowseSource[T]:
    async def fetch_page(self, offset: int, limit: int) -> Sequence[T]: ...
    async def count(self) -> int: ...
```

`ListBrowseSource` is the built-in implementation for in-memory lists. For real apps, implement `BrowseSource` directly to query your database with `LIMIT`/`OFFSET`.

The query method supports DI — add `compose.Node` parameters to inject databases, the current user, or anything from your scope:

```python
@classmethod
@query
async def fetch(cls, uid: Annotated[int, compose.Node(UserId)],
                db: Annotated[TaskDB, compose.Node(TaskDBNode)]) -> BrowseSource[TaskCard]:
    return ListBrowseSource(await db.for_user(uid))
```

### @action — what users can do

Each `@action` becomes a button below the entity card:

```python
@classmethod
@action("Delete", row=1)
async def delete(cls, task: TaskCard, db: TaskDB) -> ActionResult:
    await db.delete(task.id)
    return ActionResult.refresh("Deleted.")
```

The `row` parameter groups buttons — actions with the same `row` appear on the same line. The method receives the entity instance plus any DI dependencies.

### ActionResult

After an action runs, you tell teleflow what should happen next:

| Variant | What happens |
|---------|-------------|
| `ActionResult.refresh(message)` | Re-fetch and re-render the current page. Optional toast message. |
| `ActionResult.stay(message)` | Show a message without touching the page. Good for info alerts. |
| `ActionResult.redirect(command)` | Jump to another command entirely. |
| `ActionResult.confirm(prompt)` | Show a Yes/No dialog first, then re-call the action with `confirmed=True`. |

Confirmation is a common pattern for destructive actions:

```python
@classmethod
@action("Delete")
async def delete(cls, task: TaskCard, confirmed: bool = False) -> ActionResult:
    if not confirmed:
        return ActionResult.confirm(f"Delete '{task.title}'?")
    # ... actually delete
    return ActionResult.refresh("Deleted.")
```

### @format_card — controlling how cards look

Without `@format_card`, teleflow renders all fields as `field: value` lines. With it, you control the output:

```python
@classmethod
@format_card
def render(cls, task: TaskCard) -> str:
    return f"<b>{task.title}</b>\nStatus: {task.status}"
```

The return value is HTML-formatted text (Telegram's HTML parse mode).

### @view_filter — filter tabs

Add filter tabs above the card list. They appear as a row of buttons, and the active one is highlighted:

```python
from teleflow.browse import view_filter

@classmethod
@view_filter("Active", key="active")
@view_filter("Done", key="done")
@view_filter("All")
@query
async def fetch(cls, db: TaskDB, filter_key: str = "") -> BrowseSource[TaskCard]:
    if filter_key == "active":
        return ListBrowseSource(await db.active())
    if filter_key == "done":
        return ListBrowseSource(await db.done())
    return ListBrowseSource(await db.all())
```

Stack `@view_filter` decorators on the `@query` method. Each one declares a label and a key. The key is passed as `filter_key` to your query. The filter with no `key` (or `key=""`) is the "show all" default.

## Dashboard

Dashboard is browse for a single entity — no pagination, just one card with actions. Perfect for status pages, game tables, and user profiles.

```python
from teleflow.dashboard import tg_dashboard

@derive(tg.dashboard("profile", description="My profile"))
@dataclass
class UserProfile:
    id: Annotated[int, Identity]
    username: str
    score: int

    @classmethod
    @query
    async def fetch(cls, uid: Annotated[int, compose.Node(UserId)],
                    db: UserDB) -> UserProfile:
        return await db.get(uid)

    @classmethod
    @format_card
    def render(cls, p: UserProfile) -> str:
        return f"<b>{p.username}</b>\nScore: {p.score}"

    @classmethod
    @action("Reset score")
    async def reset(cls, profile: UserProfile, db: UserDB) -> ActionResult:
        await db.reset_score(profile.id)
        return ActionResult.refresh("Score reset!")
```

The key difference from browse: `@query` returns the entity directly (not a `BrowseSource`). Everything else — `@action`, `@format_card`, `@view_filter` — works identically.

Dashboard parameters are the same as browse minus `page_size`.

## Search

Search starts with a text prompt, then shows paginated results. It's browse with a search step prepended.

```python
from teleflow.search import tg_search

@derive(tg_search(
    command="find",
    key_node=UserId,
    prompt="What are you looking for?",
    description="Search items",
))
@dataclass
class ItemCard:
    id: Annotated[int, Identity]
    name: str

    @classmethod
    @query
    async def fetch(cls, search_query: str = "") -> BrowseSource[ItemCard]:
        return ListBrowseSource(await db.search(search_query))
```

The flow: `/find` -> bot asks "What are you looking for?" -> user types "laptop" -> bot shows matching items with pagination.

Search has all browse parameters plus one extra:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | `str` | `"What are you looking for?"` | The search prompt |

Note: search uses the standalone `tg_search()` function — it's not available through `TGApp` as a method.

---

**Prev: [Flows & Widgets](flows.md)** | **Next: [Settings](settings.md)**

[Docs index](readme.md)
