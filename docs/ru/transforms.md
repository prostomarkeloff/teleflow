# Трансформы flow

Трансформы добавляют сквозное поведение к flow — отмену, навигацию назад, индикатор прогресса, вложенные flow. Применяются через `.chain()`:

```python
from teleflow.flow import tg_flow, with_cancel, with_back, with_progress

@derive(tg.flow("register", description="Регистрация").chain(
    with_cancel(),
    with_back(),
    with_progress(),
))
@dataclass
class Registration:
    name: Annotated[str, TextInput("Имя?")]
    age: Annotated[int, Counter("Возраст?")]
    ...
```

## with_cancel()

Добавляет поддержку `/cancel`. В любой момент flow пользователь может отправить `/cancel` — состояние очищается, отправляется сообщение об отмене.

```python
@derive(tg.flow("order").chain(with_cancel()))
```

## with_back()

Добавляет поддержку `/back`. Пользователь может вернуться к предыдущему полю и ответить заново. Навигация пропускает `When`-поля, которые были скрыты.

```python
@derive(tg.flow("survey").chain(with_back()))
```

## with_progress()

Добавляет визуальный индикатор прогресса:

```
████░░░░░░ 4/10

Как вас зовут?
```

```python
@derive(tg.flow("onboarding").chain(with_progress()))
```

## with_summary()

Добавляет автоматический шаг подтверждения после сбора всех полей. Пользователь видит сводку ответов и должен подтвердить перед вызовом `finish()`.

```python
@derive(tg.flow("application").chain(with_summary()))
```

## with_show_mode(mode)

Переопределяет ShowMode flow:

```python
from teleflow.flow import ShowMode

@derive(tg.flow("wizard").chain(with_show_mode(ShowMode.EDIT)))
```

| Режим | Поведение |
|-------|-----------|
| `SEND` | Новое сообщение на промпт (по умолчанию) |
| `EDIT` | Редактирование предыдущего сообщения |
| `DELETE_AND_SEND` | Удаление старого + отправка нового |

## with_launch_mode(mode)

Переопределяет LaunchMode — что происходит при повторной отправке команды во время активного flow:

```python
from teleflow.flow import LaunchMode

@derive(tg.flow("quiz").chain(with_launch_mode(LaunchMode.EXCLUSIVE)))
```

| Режим | Поведение |
|-------|-----------|
| `STANDARD` | Текст команды как ввод поля |
| `RESET` | Перезапуск с начала |
| `EXCLUSIVE` | Блокировка — «уже запущено» |
| `SINGLE_TOP` | Повторная отправка текущего промпта |

## with_stacking(stack)

Включает навигацию вложенных flow. Flow может положить себя в стек и запустить другой flow. Когда вложенный flow завершается, родительский возобновляется.

```python
from teleflow.flow import with_stacking, FlowStack, FinishResult

stack = FlowStack()  # в памяти, или реализуйте FlowStackStorage для персистентности

@derive(tg.flow("create_project").chain(with_stacking(stack)))
@dataclass
class CreateProject:
    name: Annotated[str, TextInput("Название проекта?")]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.sub_flow("Проект создан! Теперь пригласите участников.", command="invite"))


@derive(tg.flow("invite").chain(with_stacking(stack)))
@dataclass
class InviteMembers:
    email: Annotated[str, TextInput("Email для приглашения?")]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message("Приглашено!"))
        # После этого родительский flow "create_project" возобновится
```

Кастомный бэкенд хранения:

```python
from teleflow.flow import FlowStackStorage, StackFrame

class RedisFlowStack:
    async def push(self, key: str, frame: StackFrame) -> None: ...
    async def pop(self, key: str) -> StackFrame | None: ...
```

## Комбинирование трансформов

Трансформы естественно комбинируются — порядок не важен:

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
    ...
```
