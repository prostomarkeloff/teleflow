# Browse, Dashboard и Search

teleflow предоставляет три паттерна для отображения сущностей — каждый под свой сценарий взаимодействия.

## Browse — списки с пагинацией

`tg_browse()` компилирует класс сущности в постраничный список карточек с навигацией и кнопками действий.

```python
from teleflow.browse import tg_browse, query, action, format_card, ActionResult, BrowseSource

@derive(tg.browse("tasks", page_size=5, description="Мои задачи"))
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

При отправке `/tasks` бот показывает первую страницу карточек с кнопками prev/next.

### Параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `command` | `str` | обязателен | Команда Telegram |
| `key_node` | `type` | обязателен | nodnod-нода для маршрутизации |
| `page_size` | `int` | `5` | Элементов на странице |
| `empty_text` | `str` | `"Nothing found."` | Текст при пустом списке |
| `*caps` | `SurfaceCapability` | `()` | Дополнительные capabilities |
| `cb_prefix` | `str` | `""` | Префикс callback (авто если пусто) |
| `description` | `str \| None` | `None` | Текст для help |
| `order` | `int` | `100` | Порядок в help |
| `theme` | `UITheme` | default | Настройка UI |

### @query — источник данных

Помечает classmethod как провайдер данных. Должен возвращать `BrowseSource[T]`:

```python
@classmethod
@query
async def fetch(cls, db: TaskDB) -> BrowseSource[TaskCard]:
    return ListBrowseSource(await db.all())
```

`BrowseSource` — протокол с двумя методами:

```python
class BrowseSource[T]:
    async def fetch_page(self, offset: int, limit: int) -> Sequence[T]: ...
    async def count(self) -> int: ...
```

`ListBrowseSource` — встроенная реализация на основе списка в памяти.

Метод query может принимать compose.Node-зависимости (инжектятся через DI). Также может принимать параметр `filter_key: str` для поддержки вкладок фильтрации.

### @action — действия над сущностью

Добавляют кнопки действий к каждой карточке:

```python
@classmethod
@action("Завершить", row=0)
async def complete(cls, entity: TaskCard, db: TaskDB) -> ActionResult:
    await db.mark_done(entity.id)
    return ActionResult.refresh("Готово!")
```

Параметр `row` управляет группировкой — действия с одинаковым row появляются на одной строке.

### Варианты ActionResult

| Вариант | Эффект |
|---------|--------|
| `ActionResult.refresh(message)` | Перерисовать страницу с уведомлением |
| `ActionResult.redirect(command, ...)` | Переход к другой команде |
| `ActionResult.stay(message)` | Алерт без изменения страницы |
| `ActionResult.confirm(prompt)` | Показать подтверждение Да/Нет |

Для подтверждения объявите `confirmed: bool = False` в сигнатуре:

```python
@classmethod
@action("Удалить", row=1)
async def delete(cls, entity: TaskCard, db: TaskDB, confirmed: bool = False) -> ActionResult:
    if not confirmed:
        return ActionResult.confirm(f"Удалить '{entity.title}'?")
    await db.delete(entity.id)
    return ActionResult.refresh("Удалено.")
```

### @format_card — кастомный рендеринг

```python
@classmethod
@format_card
def render(cls, entity: TaskCard) -> str:
    icon = "✅" if entity.status == "done" else "📋"
    return f"{icon} *{entity.title}*\n_{entity.status}_"
```

Без `@format_card` используется рендерер по умолчанию (все поля как `field: value`).

### @view_filter — вкладки фильтрации

```python
@view_filter("Все")
@view_filter("Активные", key="active")
@view_filter("Готовые", key="done")
@classmethod
@query
async def fetch(cls, db: TaskDB, filter_key: str = "") -> BrowseSource[TaskCard]:
    if filter_key == "active":
        return ListBrowseSource(await db.active())
    elif filter_key == "done":
        return ListBrowseSource(await db.done())
    return ListBrowseSource(await db.all())
```

Вкладки отображаются как кнопки над навигацией. Активная вкладка выделена.

---

## Dashboard — карточка одной сущности

`tg_dashboard()` — как browse, но показывает ровно одну сущность, без пагинации. Идеален для статус-страниц, игровых столов, профилей.

```python
from teleflow.dashboard import tg_dashboard

@derive(tg.dashboard("profile", description="Мой профиль"))
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
    @action("Сбросить счёт")
    async def reset(cls, entity: UserProfile, db: UserDB) -> ActionResult:
        await db.reset_score(entity.id)
        return ActionResult.refresh("Счёт сброшен!")
```

Ключевое отличие: `@query` возвращает сущность напрямую (или `None`), а не `BrowseSource`.

Dashboard поддерживает те же декораторы — `@action`, `@format_card`, `@view_filter`.

### Параметры

Как у browse, без `page_size`.

---

## Search — поиск с пагинацией

`tg_search()` начинается с поискового запроса. Пользователь вводит текст, затем видит результаты с пагинацией.

```python
from teleflow.search import tg_search

@derive(tg.search("find", prompt="Что ищете?", description="Поиск"))
@dataclass
class ItemCard:
    id: Annotated[int, Identity]
    name: str

    @classmethod
    @query
    async def fetch(cls, db: ItemDB, search_query: str = "") -> BrowseSource[ItemCard]:
        return ListBrowseSource(await db.search(search_query))
```

Сценарий: `/find` → бот спрашивает «Что ищете?» → пользователь пишет «ноутбук» → бот показывает результаты.

### Параметры

Как у browse, плюс:

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `prompt` | `str` | `"What are you looking for?"` | Текст поискового запроса |

Search использует всю инфраструктуру browse — `@action`, `@format_card`, `@view_filter` работают.
