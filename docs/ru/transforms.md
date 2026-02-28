# Трансформы

Голый flow работает, но реальные пользователи ожидают большего — возможность отменить, вернуться к предыдущему вопросу, видеть свой прогресс. Трансформы добавляют эти поведения, не затрагивая логику flow.

Применяйте трансформы через `.chain()`:

```python
from teleflow.flow import with_cancel, with_back, with_progress

@derive(tg.flow("register", description="Регистрация").chain(
    with_cancel(),
    with_back(),
    with_progress(),
))
@dataclass
class Registration:
    ...
```

Каждый трансформ оборачивает flow дополнительной обработкой. Они свободно комбинируются — порядок не важен, можно складывать сколько угодно.

## with_cancel()

Самый важный трансформ. Позволяет пользователю отправить `/cancel` в любой момент для прерывания flow. Состояние очищается, отправляется сообщение об отмене.

```python
@derive(tg.flow("order").chain(with_cancel()))
```

Без этого пользователь, застрявший в flow, может только ждать истечения сессии.

## with_back()

Добавляет поддержку `/back`. Пользователь отправляет `/back` и возвращается к предыдущему полю, чтобы ответить заново. Навигация умная — пропускает `When`-условные поля, которые были скрыты.

```python
@derive(tg.flow("survey").chain(with_back()))
```

Хорошо сочетается с `with_cancel()` для полноценной навигации.

## with_progress()

Показывает визуальный прогресс-бар над каждым промптом:

```
████░░░░░░ 4/10

Как вас зовут?
```

Полезно для длинных flows, чтобы пользователь знал, сколько осталось.

```python
@derive(tg.flow("onboarding").chain(with_progress()))
```

## with_summary()

Добавляет автоматический шаг подтверждения после сбора всех полей. Пользователь видит сводку ответов и должен подтвердить перед вызовом `finish()`. При отказе flow перезапускается.

```python
@derive(tg.flow("application").chain(with_summary()))
```

## with_show_mode(mode) и with_launch_mode(mode)

Переопределяют `ShowMode` или `LaunchMode` flow через трансформ вместо установки в объявлении паттерна. Полезно, когда один класс паттерна используется с разными режимами:

```python
from teleflow.flow import ShowMode, LaunchMode

@derive(tg.flow("wizard").chain(
    with_show_mode(ShowMode.EDIT),
    with_launch_mode(LaunchMode.EXCLUSIVE),
))
```

Описание режимов — в [Flows и виджеты](flows.md).

## with_stacking(stack)

Самый мощный трансформ. Включает навигацию вложенных flow — один flow может приостановить себя, запустить другой и возобновиться, когда дочерний завершится.

```python
from teleflow.flow import with_stacking, FlowStack, FinishResult

stack = FlowStack()  # в памяти; реализуйте FlowStackStorage для персистентности

@derive(tg.flow("create_project").chain(with_stacking(stack)))
@dataclass
class CreateProject:
    name: Annotated[str, TextInput("Название проекта?")]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.sub_flow(
            "Проект создан! Теперь пригласите участников.",
            command="invite",
        ))


@derive(tg.flow("invite").chain(with_stacking(stack)))
@dataclass
class InviteMembers:
    email: Annotated[str, TextInput("Email для приглашения?")]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message("Приглашено!"))
        # родительский flow "create_project" возобновляется автоматически
```

Оба flow должны разделять один экземпляр `FlowStack` и оба должны иметь `with_stacking()`.

`FinishResult.sub_flow(text, command="child")` кладёт текущий flow в стек и запускает дочерний. Когда дочерний вызывает `FinishResult.message(...)`, стек извлекается и родительский продолжает.

Для продакшена реализуйте `FlowStackStorage` для персистентного хранения стека (напр., в Redis):

```python
from teleflow.flow import FlowStackStorage, StackFrame

class RedisFlowStack:
    async def push(self, key: str, frame: StackFrame) -> None: ...
    async def pop(self, key: str) -> StackFrame | None: ...
```

## Всё вместе

Полностью оснащённый flow:

```python
@derive(tg.flow("full_wizard").chain(
    with_cancel(),
    with_back(),
    with_progress(),
    with_summary(),
    with_show_mode(ShowMode.EDIT),
    with_stacking(stack),
))
@dataclass
class FullWizard:
    name: Annotated[str, TextInput("Имя?")]
    email: Annotated[str, TextInput("Email?"), Pattern(r"^[\w.]+@[\w.]+$")]
    plan: Annotated[str, Inline("Тариф:", free="Бесплатный", pro="Pro")]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message(f"Добро пожаловать, {self.name}!"))
```

Этот flow имеет: поддержку отмены, навигацию назад, прогресс-бар, сводку для подтверждения, чистое редактирование сообщений и возможность запуска вложенных flows. Всё из шести вызовов трансформов.

---

**Назад: [Settings](settings.md)** | **Далее: [Темизация](theming.md)**

[Оглавление](readme.md)
