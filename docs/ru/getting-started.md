# Начало работы

teleflow превращает аннотированные Python-датаклассы в полноценные интерактивные Telegram-интерфейсы. Вы описываете *что* собирает бот — teleflow генерирует обработчики, клавиатуры, пагинацию и управление сессиями.

## Установка

```bash
uv add teleflow --git https://github.com/prostomarkeloff/teleflow
```

Требуется Python 3.14+. Зависит от [emergent](https://github.com/prostomarkeloff/emergent) и [telegrinder](https://github.com/timoniq/telegrinder).

## Первый бот

Каждое teleflow-приложение начинается с `TGApp` — координатора, который владеет всеми паттернами и следит за уникальностью команд.

```python
from dataclasses import dataclass
from typing import Annotated

from kungfu import Ok, Result
from derivelib import derive
from derivelib._errors import DomainError
from teleflow.app import TGApp
from teleflow.flow import TextInput, Counter, FinishResult

# 1. Создаём приложение
tg = TGApp(key_node=UserId)


# 2. Объявляем flow
@derive(tg.flow("register", description="Регистрация"))
@dataclass
class Registration:
    name: Annotated[str, TextInput("Как вас зовут?")]
    age: Annotated[int, Counter("Сколько вам лет?", min=1, max=120)]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message(f"Добро пожаловать, {self.name}!"))
```

Когда пользователь отправляет `/register`, бот проведёт его через два шага — текстовый ввод имени и счётчик +/- для возраста — затем вызовет `finish()`.

## Компиляция в Dispatch

Паттерны teleflow компилируются в telegrinder `Dispatch` через wire-компилятор emergent:

```python
from emergent.wire.axis.surface._app import build_application_from_decorated
from telegrinder import API, Telegrinder

# Собираем wire-приложение из всех @derive-декорированных классов
app = build_application_from_decorated(Registration)

# Компилируем в telegrinder Dispatch
dp = tg.compile(app)

# Запускаем бота
bot = Telegrinder(API(token="BOT_TOKEN"), dispatch=dp)
bot.run_forever()
```

## Добавляем browse-представление

Покажите пользователям список сущностей с пагинацией:

```python
from teleflow.browse import BrowseSource, query, action, ActionResult

@derive(tg.browse("tasks", description="Мои задачи"))
@dataclass
class TaskCard:
    id: Annotated[int, Identity]
    title: str
    done: bool

    @classmethod
    @query
    async def fetch(cls, db: TaskDB) -> BrowseSource[TaskCard]:
        return ListBrowseSource(await db.all())

    @classmethod
    @action("Завершить")
    async def complete(cls, entity: TaskCard, db: TaskDB) -> ActionResult:
        await db.mark_done(entity.id)
        return ActionResult.refresh("Готово!")
```

`/tasks` показывает список карточек с навигацией prev/next и кнопкой «Завершить» на каждой карточке.

## Что дальше

- [Flows и виджеты](flows.md) — все типы виджетов, валидация, динамические опции
- [Browse, Dashboard и Search](views.md) — представления сущностей
- [Settings](settings.md) — редактирование настроек
- [Трансформы](transforms.md) — отмена, назад, прогресс, вложенные flow
- [Темизация](theming.md) — настройка строк и иконок
