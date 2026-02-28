# Browse, Dashboard & Search

teleflow provides three patterns for displaying entities to users — each tailored to a different interaction style.

## Browse — paginated lists

`tg_browse()` compiles an entity class into a paginated card list with navigation and action buttons.

```python
from teleflow.browse import tg_browse, query, action, format_card, ActionResult, BrowseSource

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
```

When a user sends `/tasks`, the bot renders the first page of cards with prev/next buttons.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `command` | `str` | required | Telegram command |
| `key_node` | `type` | required | nodnod session routing node |
| `page_size` | `int` | `5` | Items per page |
| `empty_text` | `str` | `"Nothing found."` | Shown when no items |
| `*caps` | `SurfaceCapability` | `()` | Additional capabilities |
| `cb_prefix` | `str` | `""` | Custom callback prefix (auto-generated if empty) |
| `description` | `str \| None` | `None` | Help text |
| `order` | `int` | `100` | Sort order in help |
| `theme` | `UITheme` | default | UI customization |

### @query — data source

Mark a classmethod as the data provider. Must return a `BrowseSource[T]`:

```python
@classmethod
@query
async def fetch(cls, db: TaskDB) -> BrowseSource[TaskCard]:
    return ListBrowseSource(await db.all())
```

`BrowseSource` is a protocol with two methods:

```python
class BrowseSource[T]:
    async def fetch_page(self, offset: int, limit: int) -> Sequence[T]: ...
    async def count(self) -> int: ...
```

`ListBrowseSource` is a built-in implementation backed by an in-memory list.

The query method can accept compose.Node dependencies (injected via DI). It can also accept a `filter_key: str` parameter for filter tab support.

### @action — entity actions

Add action buttons to each card:

```python
@classmethod
@action("Complete", row=0)
async def complete(cls, entity: TaskCard, db: TaskDB) -> ActionResult:
    await db.mark_done(entity.id)
    return ActionResult.refresh("Marked as done!")
```

The `row` parameter controls button grouping — actions with the same row appear on the same line.

Action methods receive the entity instance and can accept compose.Node dependencies.

### ActionResult variants

| Variant | Effect |
|---------|--------|
| `ActionResult.refresh(message)` | Re-render current page with a toast message |
| `ActionResult.redirect(command, ...)` | Switch to another command |
| `ActionResult.stay(message)` | Show alert without changing the page |
| `ActionResult.confirm(prompt)` | Show Yes/No confirmation before executing |

For confirmation, declare `confirmed: bool = False` in the action signature:

```python
@classmethod
@action("Delete", row=1)
async def delete(cls, entity: TaskCard, db: TaskDB, confirmed: bool = False) -> ActionResult:
    if not confirmed:
        return ActionResult.confirm(f"Delete '{entity.title}'?")
    await db.delete(entity.id)
    return ActionResult.refresh("Deleted.")
```

### @format_card — custom rendering

Override the default card renderer:

```python
@classmethod
@format_card
def render(cls, entity: TaskCard) -> str:
    icon = "✅" if entity.status == "done" else "📋"
    return f"{icon} *{entity.title}*\n_{entity.status}_"
```

Without `@format_card`, the default renderer shows all fields as `field: value` lines.

### @view_filter — filter tabs

Add tab buttons for filtering:

```python
@view_filter("All")
@view_filter("Active", key="active")
@view_filter("Done", key="done")
@classmethod
@query
async def fetch(cls, db: TaskDB, filter_key: str = "") -> BrowseSource[TaskCard]:
    if filter_key == "active":
        return ListBrowseSource(await db.active())
    elif filter_key == "done":
        return ListBrowseSource(await db.done())
    return ListBrowseSource(await db.all())
```

Filter tabs appear as buttons above the navigation. The active tab is highlighted.

---

## Dashboard — single-entity cards

`tg_dashboard()` is like browse but shows exactly one entity — no pagination. Ideal for status pages, game tables, user profiles.

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
    async def fetch(cls, db: UserDB, uid: UserId) -> UserProfile | None:
        return await db.get(uid.value)

    @classmethod
    @action("Reset score")
    async def reset(cls, entity: UserProfile, db: UserDB) -> ActionResult:
        await db.reset_score(entity.id)
        return ActionResult.refresh("Score reset!")
```

The key difference: `@query` returns the entity directly (or `None`), not a `BrowseSource`.

Dashboard supports the same decorators — `@action`, `@format_card`, `@view_filter` — with identical semantics.

### Parameters

Same as browse, minus `page_size`.

---

## Search — search-first browsing

`tg_search()` starts with a search prompt. The user types a query, then sees paginated results.

```python
from teleflow.search import tg_search

@derive(tg.search("find", prompt="What are you looking for?", description="Search items"))
@dataclass
class ItemCard:
    id: Annotated[int, Identity]
    name: str

    @classmethod
    @query
    async def fetch(cls, db: ItemDB, search_query: str = "") -> BrowseSource[ItemCard]:
        return ListBrowseSource(await db.search(search_query))
```

Flow: `/find` → bot asks "What are you looking for?" → user types "laptop" → bot shows matching items with pagination.

### Parameters

Same as browse, plus:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | `str` | `"What are you looking for?"` | The search prompt message |

Search reuses the full browse infrastructure — `@action`, `@format_card`, `@view_filter` all work.
