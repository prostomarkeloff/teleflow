# Начало работы

teleflow превращает Python-датаклассы в Telegram-ботов. Аннотируете поля виджетами, а teleflow генерирует обработчики, клавиатуры, пагинацию и управление сессиями. Никакого ручного роутинга колбэков, никаких стейт-машин — просто объявление и деривация.

## Установка

```bash
uv add teleflow --git https://github.com/prostomarkeloff/teleflow
```

Требуется Python 3.14+. Автоматически подтягивает [emergent](https://github.com/prostomarkeloff/emergent) и [telegrinder](https://github.com/timoniq/telegrinder).

## Первый flow

Самое простое, что можно построить — это **flow**, многошаговый диалог. Бот задаёт вопросы по очереди, собирает ответы в типизированный датакласс и вызывает ваш метод `finish()`.

```python
from dataclasses import dataclass
from typing import Annotated

from kungfu import Ok, Result
from telegrinder.node import UserId
from derivelib import derive
from derivelib._errors import DomainError

from teleflow.app import TGApp
from teleflow.flow import TextInput, Counter, FinishResult

tg = TGApp(key_node=UserId)

@derive(tg.flow("greet", description="Приветствие"))
@dataclass
class Greeting:
    name: Annotated[str, TextInput("Как вас зовут?")]
    age: Annotated[int, Counter("Сколько вам лет?", min=1, max=120)]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message(f"Привет, {self.name}! {self.age} — отличный возраст."))
```

Когда пользователь отправляет `/greet`, бот спрашивает "Как вас зовут?" и ждёт ответа. Пользователь отвечает текстом — это становится `self.name`. Затем бот показывает `+`/`-` счётчик для возраста. После заполнения обоих полей вызывается `finish()` и отправляется сообщение.

`TGApp` — координатор. Он владеет всеми паттернами, следит за уникальностью команд и разделяет тему и реестр колбэков между всем.

## Добавляем browse

Flows собирают данные. **Browse** отображает их. Вот пагинированный список с кнопками действий:

```python
from emergent.wire.axis.schema import Identity
from teleflow.browse import ListBrowseSource, BrowseSource, ActionResult, query, action, format_card

@derive(tg.browse("items", page_size=3, description="Элементы"))
@dataclass
class ItemCard:
    id: Annotated[int, Identity]
    title: str
    done: bool

    @classmethod
    @query
    async def fetch(cls) -> BrowseSource[ItemCard]:
        return ListBrowseSource([
            ItemCard(1, "Написать документацию", False),
            ItemCard(2, "Выпустить v1", False),
        ])

    @classmethod
    @format_card
    def render(cls, item: ItemCard) -> str:
        icon = "готово" if item.done else "в работе"
        return f"[{icon}] {item.title}"

    @classmethod
    @action("Завершить")
    async def complete(cls, item: ItemCard) -> ActionResult:
        return ActionResult.refresh(f"Завершено: {item.title}")
```

`/items` показывает первую страницу карточек с кнопками пагинации и действием «Завершить» на каждой. Поле `id` с аннотацией `Identity` указывает teleflow, какое поле уникально идентифицирует сущность.

## Компиляция и запуск

Паттерны teleflow не создают обработчики напрямую. Они описывают **application** — переносимое представление, которое компилируется под конкретный рантайм. Для Telegram этот рантайм — telegrinder:

```python
from derivelib import build_application_from_decorated
from telegrinder import API, Telegrinder, Token
from emergent.wire.compile.targets import telegrinder as tg_compile

# Собираем все @derive-классы в wire application
app = build_application_from_decorated(Greeting, ItemCard)

# Компилируем в telegrinder Dispatch
dp = tg_compile.compile(app)

# Запускаем
bot = Telegrinder(API(Token("YOUR_BOT_TOKEN")), dispatch=dp)
bot.run_forever()
```

Этот двухэтапный процесс (собрать application, скомпилировать) — ключ архитектуры emergent. Application не зависит от цели — те же `@derive`-объявления могут компилироваться в HTTP или CLI. Для teleflow цель всегда telegrinder.

## Что дальше

Вы познакомились с двумя основными паттернами — flow для сбора данных и browse для их отображения. В teleflow ещё три паттерна (dashboard, settings, search) и богатая библиотека виджетов. Продолжайте:

**Далее: [Flows и виджеты](flows.md)** — полный каталог виджетов, валидация, условные поля и кастомные виджеты

---

[Оглавление](readme.md)
