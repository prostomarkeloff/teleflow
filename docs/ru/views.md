# Представления: Browse, Dashboard и Search

Flows собирают данные. Представления показывают данные пользователям. В teleflow три паттерна представлений — каждый отвечает на свой вопрос.

**Browse**: «Вот список вещей. Листай, делай что-нибудь.» \
**Dashboard**: «Вот одна вещь. Смотри, делай что-нибудь.» \
**Search**: «Что ищешь?» Затем browse по результатам.

Все три используют одни декораторы (`@query`, `@action`, `@format_card`, `@view_filter`) и одну систему `ActionResult`. Выучив один, легко освоите остальные.

## Browse

Рабочая лошадка. Берёт класс-сущность и компилирует его в пагинированные карточки с навигацией и кнопками действий.

```python
from emergent.wire.axis.schema import Identity
from teleflow.browse import ListBrowseSource, BrowseSource, ActionResult, query, action, format_card

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

    @classmethod
    @format_card
    def render(cls, task: TaskCard) -> str:
        icon = "готово" if task.status == "done" else "открыто"
        return f"[{icon}] <b>{task.title}</b>"

    @classmethod
    @action("Завершить", row=0)
    async def complete(cls, task: TaskCard, db: TaskDB) -> ActionResult:
        await db.mark_done(task.id)
        return ActionResult.refresh("Отмечено как выполненное!")
```

Пользователь отправляет `/tasks` и видит первую страницу с кнопками вперёд/назад. На каждой карточке — отформатированный текст и кнопки действий.

### Параметры browse

| Параметр | Тип | Значение | Описание |
|----------|-----|----------|----------|
| `command` | `str` | обязателен | Команда Telegram |
| `page_size` | `int` | `5` | Элементов на странице |
| `empty_text` | `str` | `"Nothing found."` | Показывается при отсутствии данных |
| `description` | `str \| None` | `None` | Текст для help |
| `order` | `int` | `100` | Позиция в help |
| `cb_prefix` | `str` | `""` | Кастомный префикс колбэков (генерируется, если пустой) |

### @query — источник данных

Классметод `@query` — источник данных. Должен возвращать `BrowseSource[T]` — протокол с двумя методами:

```python
class BrowseSource[T]:
    async def fetch_page(self, offset: int, limit: int) -> Sequence[T]: ...
    async def count(self) -> int: ...
```

`ListBrowseSource` — встроенная реализация для списков в памяти. Для реальных приложений реализуйте `BrowseSource` напрямую с `LIMIT`/`OFFSET` запросами к базе.

Метод query поддерживает DI — добавьте параметры `compose.Node` для инъекции баз данных, текущего пользователя или чего угодно из скоупа:

```python
@classmethod
@query
async def fetch(cls, uid: Annotated[int, compose.Node(UserId)],
                db: Annotated[TaskDB, compose.Node(TaskDBNode)]) -> BrowseSource[TaskCard]:
    return ListBrowseSource(await db.for_user(uid))
```

### @action — действия пользователей

Каждый `@action` становится кнопкой под карточкой:

```python
@classmethod
@action("Удалить", row=1)
async def delete(cls, task: TaskCard, db: TaskDB) -> ActionResult:
    await db.delete(task.id)
    return ActionResult.refresh("Удалено.")
```

Параметр `row` группирует кнопки — действия с одинаковым `row` отображаются в одной строке. Метод получает экземпляр сущности плюс DI-зависимости.

### ActionResult

После выполнения действия вы сообщаете teleflow, что должно произойти:

| Вариант | Что происходит |
|---------|---------------|
| `ActionResult.refresh(message)` | Перезагрузить и перерисовать текущую страницу. Опциональное уведомление. |
| `ActionResult.stay(message)` | Показать сообщение, не трогая страницу. Для информационных алертов. |
| `ActionResult.redirect(command)` | Перейти к другой команде. |
| `ActionResult.confirm(prompt)` | Показать диалог Да/Нет, затем повторно вызвать действие с `confirmed=True`. |

Подтверждение — типичный паттерн для деструктивных действий:

```python
@classmethod
@action("Удалить")
async def delete(cls, task: TaskCard, confirmed: bool = False) -> ActionResult:
    if not confirmed:
        return ActionResult.confirm(f"Удалить '{task.title}'?")
    # ... реально удаляем
    return ActionResult.refresh("Удалено.")
```

### @format_card — управление отображением

Без `@format_card` teleflow рендерит все поля как строки `поле: значение`. С ним вы контролируете вывод:

```python
@classmethod
@format_card
def render(cls, task: TaskCard) -> str:
    return f"<b>{task.title}</b>\nСтатус: {task.status}"
```

Возвращаемое значение — HTML-текст (HTML parse mode Telegram).

### @view_filter — вкладки фильтрации

Добавляет вкладки-фильтры над списком карточек. Отображаются как строка кнопок, активная выделена:

```python
from teleflow.browse import view_filter

@classmethod
@view_filter("Активные", key="active")
@view_filter("Готовые", key="done")
@view_filter("Все")
@query
async def fetch(cls, db: TaskDB, filter_key: str = "") -> BrowseSource[TaskCard]:
    if filter_key == "active":
        return ListBrowseSource(await db.active())
    if filter_key == "done":
        return ListBrowseSource(await db.done())
    return ListBrowseSource(await db.all())
```

`@view_filter` декораторы ставятся на `@query` метод. Каждый объявляет метку и ключ. Ключ передаётся как `filter_key` в query. Фильтр без `key` (или `key=""`) — показ всего по умолчанию.

## Dashboard

Dashboard — browse для одной сущности. Без пагинации, одна карточка с действиями. Идеально для страниц статуса, игровых столов и профилей.

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
    async def fetch(cls, uid: Annotated[int, compose.Node(UserId)],
                    db: UserDB) -> UserProfile:
        return await db.get(uid)

    @classmethod
    @format_card
    def render(cls, p: UserProfile) -> str:
        return f"<b>{p.username}</b>\nСчёт: {p.score}"

    @classmethod
    @action("Сбросить счёт")
    async def reset(cls, profile: UserProfile, db: UserDB) -> ActionResult:
        await db.reset_score(profile.id)
        return ActionResult.refresh("Счёт сброшен!")
```

Ключевое отличие от browse: `@query` возвращает сущность напрямую (не `BrowseSource`). Всё остальное — `@action`, `@format_card`, `@view_filter` — работает идентично.

Параметры dashboard — те же, что у browse, минус `page_size`.

## Search

Search начинается с текстового запроса, затем показывает пагинированные результаты. Это browse с добавленным шагом поиска.

```python
from teleflow.search import tg_search

@derive(tg_search(
    command="find",
    key_node=UserId,
    prompt="Что ищете?",
    description="Поиск",
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

Процесс: `/find` -> бот спрашивает «Что ищете?» -> пользователь вводит «ноутбук» -> бот показывает результаты с пагинацией.

У search все параметры browse плюс один дополнительный:

| Параметр | Тип | Значение | Описание |
|----------|-----|----------|----------|
| `prompt` | `str` | `"What are you looking for?"` | Промпт поиска |

Примечание: search использует standalone-функцию `tg_search()` — он не доступен как метод `TGApp`.

---

**Назад: [Flows и виджеты](flows.md)** | **Далее: [Settings](settings.md)**

[Оглавление](readme.md)
