# Flows и виджеты

Flow — это диалог между ботом и пользователем. Бот задаёт вопросы, пользователь отвечает, ответы накапливаются в типизированный датакласс. Когда все поля заполнены, управление переходит к вашему методу `finish()`.

## Объявление flow

```python
from teleflow.flow import TextInput, Inline, FinishResult

@derive(tg.flow("order", description="Оформить заказ"))
@dataclass
class Order:
    item: Annotated[str, Inline("Выберите:", pizza="Пицца", burger="Бургер")]
    note: Annotated[str, TextInput("Пожелания?")]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message(f"Заказано: {self.item}!"))
```

Каждое поле аннотировано **виджетом** — элементом UI, через который бот собирает значение. Flow проходит по полям сверху вниз, по одному.

Можно использовать `tg.flow(...)` через `TGApp` (разделяет key_node, тему и проверяет уникальность), или напрямую `tg_flow(command=..., key_node=...)`. `TGApp` — рекомендуемый способ.

### Параметры flow

| Параметр | Тип | Значение | Описание |
|----------|-----|----------|----------|
| `command` | `str` | обязателен | Команда Telegram (`"order"` → `/order`) |
| `description` | `str \| None` | `None` | Текст для `/help` |
| `order` | `int` | `100` | Позиция в списке help |
| `show_mode` | `ShowMode` | `SEND` | Как отображаются промпты (см. ниже) |
| `launch_mode` | `LaunchMode` | `STANDARD` | Поведение при повторном входе (см. ниже) |

## Виджеты

Виджеты — строительные блоки. Каждый умеет отрисоваться (текст + клавиатура), обработать ввод и провалидировать результат.

### Сбор текста

**TextInput(prompt)** — самый простой виджет. Бот отправляет промпт, пользователь отвечает текстом:

```python
name: Annotated[str, TextInput("Как вас зовут?")]
```

**NumberInput(prompt, min, max, shortcuts)** ожидает число. Можно добавить кнопки быстрого выбора:

```python
amount: Annotated[int, NumberInput("Сколько?", min=1, max=100, shortcuts=(5, 10, 25))]
```

**PinInput(prompt, length, mask, secret)** — нумпад для ввода PIN-кода. Цифры отображаются замаскированными:

```python
pin: Annotated[str, PinInput("Введите PIN:", length=4, secret=True)]
```

### Выбор из вариантов

Когда нужно, чтобы пользователь выбрал из предопределённого набора:

**Inline(prompt, \*\*options)** — кнопки, один тап выбирает. Быстрый, без состояния — лучший для коротких списков:

```python
color: Annotated[str, Inline("Цвет:", red="Красный", blue="Синий", green="Зелёный")]
```

**Radio(prompt, \*\*options)** — как Inline, но показывает состояние выбора (точка отмечает текущий) и требует нажатия «Готово» для подтверждения:

```python
size: Annotated[str, Radio("Размер футболки:", s="S", m="M", l="L", xl="XL")]
```

**Multiselect(prompt, min_selected, max_selected, \*\*options)** — множественный выбор с галочками:

```python
toppings: Annotated[str, Multiselect(
    "Топпинги:",
    cheese="Сыр", mushrooms="Грибы", peppers="Перец",
    min_selected=1, max_selected=3,
)]
```

**ScrollingInline(prompt, page_size, \*\*options)** — пагинированный выбор для больших списков:

```python
country: Annotated[str, ScrollingInline("Страна:", page_size=8, **country_map)]
```

**EnumInline(prompt)** — автоматически генерирует варианты из Python Enum:

```python
class Priority(enum.Enum):
    LOW = "Низкий"
    MEDIUM = "Средний"
    HIGH = "Высокий"

priority: Annotated[Priority, EnumInline("Приоритет:")]
```

Все виджеты выбора принимают `columns: int` для управления количеством кнопок в строке (по умолчанию 1).

### Да/нет и переключатели

**Confirm(prompt)** — вопрос Да/Нет, возвращает `bool`:

```python
agree: Annotated[bool, Confirm("Принимаете условия?")]
```

**Toggle(prompt)** — переключатель в одно нажатие. Показывает текущее состояние и переключает по тапу:

```python
notifications: Annotated[bool, Toggle("Уведомления:")]
```

### Числа и диапазоны

**Counter(prompt, min, max, step, default)** — кнопки `+`/`-` для пошагового выбора целых чисел:

```python
quantity: Annotated[int, Counter("Сколько?", min=1, max=99, step=1, default=1)]
```

**Slider(prompt, min, max, step, big_step, default, presets, bar_width, filled, empty)** — визуальный прогресс-бар с точной и грубой регулировкой:

```python
volume: Annotated[int, Slider("Громкость:", min=0, max=100, step=5, big_step=20)]
```

**Rating(prompt, max_stars, filled, empty)** — звёздочки для оценки:

```python
score: Annotated[int, Rating("Оцените нас:", max_stars=5)]
```

### Даты и время

**DatePicker(prompt, min_date, max_date)** — полный календарь с навигацией по месяцам/годам:

```python
from datetime import date
birthday: Annotated[str, DatePicker("Дата рождения:", max_date=date.today())]
```

**TimePicker(prompt, min_hour, max_hour, step_minutes)** — двухэтапный выбор: сначала час, затем минуты:

```python
alarm: Annotated[str, TimePicker("Будильник:", min_hour=6, max_hour=22, step_minutes=15)]
```

**RecurrencePicker(prompt)** — выбор дней недели + времени. Возвращает строку вида `"0,2,4@10:30"` (Пн/Ср/Пт в 10:30):

```python
schedule: Annotated[str, RecurrencePicker("Расписание:")]
```

**TimeSlotPicker(prompt, columns, date_format)** — временные слоты, сгруппированные по датам, загружаемые через `@options`:

```python
slot: Annotated[str, TimeSlotPicker("Выберите слот:")]
```

### Загрузка медиа

Медиа-виджеты собирают Telegram `file_id` (кроме `LocationInput`, который собирает координаты):

```python
photo: Annotated[str, PhotoInput("Отправьте фото:")]
doc: Annotated[str, DocumentInput("Загрузите документ:")]
video: Annotated[str, VideoInput("Отправьте видео:")]
voice: Annotated[str, VoiceInput("Запишите голосовое сообщение:")]
location: Annotated[str, LocationInput("Поделитесь геолокацией:")]
contact: Annotated[str, ContactInput("Поделитесь контактом:")]
```

**MediaGroupInput(prompt, min, max, accept)** — сбор нескольких медиа-файлов:

```python
photos: Annotated[str, MediaGroupInput("Отправьте фото:", min=1, max=5, accept="photo")]
```

### Списки

**ListBuilder(prompt, min, max)** — сбор списка текстовых элементов по одному. Пользователь отправляет элементы и нажимает «Готово»:

```python
tags: Annotated[str, ListBuilder("Добавьте теги (по одному):", min=1, max=10)]
```

## Динамические опции

Иногда варианты неизвестны заранее — они приходят из базы или API. Используйте `@options("field_name")` для загрузки в рантайме:

```python
from teleflow.widget import options

@derive(tg.flow("assign", description="Назначить задачу"))
@dataclass
class AssignTask:
    assignee: Annotated[str, DynamicInline("Назначить:")]

    @classmethod
    @options("assignee")
    async def load_users(cls, db: UserDB) -> dict[str, str]:
        users = await db.all()
        return {str(u.id): u.name for u in users}
```

Метод возвращает `dict[str, str]` — ключи хранятся как значения, значения — метки для отображения. Поддерживает DI-зависимости.

Динамические варианты виджетов: `DynamicInline`, `DynamicRadio`, `DynamicMultiselect`, `TimeSlotPicker`.

## Условные поля

Не каждое поле актуально для каждого пользователя. `When()` делает поле условным — оно запрашивается только когда предикат возвращает True:

```python
from teleflow.flow import When

kind: Annotated[str, Inline("Тип:", bug="Баг", feature="Фича")]
severity: Annotated[str, Inline("Критичность:", high="Высокая", low="Низкая"),
    When(lambda state: state.get("kind") == "bug")]
```

Предикат получает `dict[str, object]` со всеми собранными значениями. Если `kind` не `"bug"`, `severity` молча пропускается.

## Валидация

Аннотации валидации ставятся рядом с виджетами — проверяются автоматически при каждом вводе:

```python
from teleflow.flow import MinLen, MaxLen, Pattern

username: Annotated[str, TextInput("Логин:"), MinLen(3), MaxLen(20)]
email: Annotated[str, TextInput("Email:"), Pattern(r"^[\w.]+@[\w.]+$")]
```

При ошибке пользователь видит сообщение (настраиваемое через тему) и получает повторный запрос.

## Завершение flow

Каждый flow должен иметь метод `finish()`. Он вызывается после сбора всех полей:

```python
async def finish(self) -> Result[FinishResult, DomainError]:
    return Ok(FinishResult.message("Готово!"))
```

Конструкторы `FinishResult` для разных сценариев:

- **`FinishResult.message(text)`** — отправить текст и завершить
- **`FinishResult.then(text, command="next")`** — ответить, затем перенаправить на другую команду
- **`FinishResult.sub_flow(text, command="child")`** — положить flow в стек и запустить дочерний (требует `with_stacking`, см. [Трансформы](transforms.md))
- **`FinishResult.with_keyboard(text, markup)`** — ответить с кастомной клавиатурой

`finish()` также может принимать DI-зависимости через аннотации `compose.Node` — доступ к базам, сервисам или текущему пользователю.

## ShowMode и LaunchMode

Два enum контролируют отображение flow:

**ShowMode** — как каждый промпт появляется в чате:

| Режим | Что происходит |
|-------|---------------|
| `ShowMode.SEND` | Новое сообщение на каждый промпт (по умолчанию). Просто и надёжно. |
| `ShowMode.EDIT` | Редактирование предыдущего сообщения. Чат остаётся чистым. |
| `ShowMode.DELETE_AND_SEND` | Удаление старого, отправка нового. Полезно при смене типа контента. |

**LaunchMode** — что происходит, когда пользователь отправляет команду во время активного flow:

| Режим | Что происходит |
|-------|---------------|
| `LaunchMode.STANDARD` | Текст команды обрабатывается как ввод для текущего поля (по умолчанию). |
| `LaunchMode.RESET` | Сброс flow и начало сначала. |
| `LaunchMode.EXCLUSIVE` | Блокировка с сообщением «уже запущено». |
| `LaunchMode.SINGLE_TOP` | Повторная отправка текущего промпта — продолжение с того же места. |

Устанавливаются на flow или переопределяются трансформами:

```python
@derive(tg.flow("quiz", show_mode=ShowMode.EDIT, launch_mode=LaunchMode.EXCLUSIVE))
```

## Специальные виджеты

**Prefilled()** — поле, заполненное из контекста, не запрашивается у пользователя:

```python
user_id: Annotated[int, Prefilled()]
```

**Case(selector, \*\*options)** — показывает разный текст промпта в зависимости от значения предыдущего поля:

```python
kind: Annotated[str, Inline("Тип:", bug="Баг", feature="Фича")]
details: Annotated[str, Case(selector="kind", bug="Опишите баг:", feature="Опишите фичу:")]
```

**SummaryReview(\*\*labels)** — отображает все собранные значения для подтверждения:

```python
confirm: Annotated[bool, SummaryReview(name="Имя", age="Возраст")]
```

**Either(primary, secondary)** — пробует основной виджет, при неудаче использует запасной:

```python
input: Annotated[str, Either(PhotoInput("Отправьте фото:"), TextInput("Или опишите текстом:"))]
```

## Кастомные виджеты

Если встроенных виджетов недостаточно, реализуйте протокол `FlowWidget`:

```python
from teleflow.widget import WidgetContext, Advance, Reject, NoOp

class ColorPicker:
    @property
    def prompt(self) -> str:
        return "Выберите цвет:"

    @property
    def needs_callback(self) -> bool:
        return True  # виджет использует инлайн-клавиатуру

    async def render(self, ctx: WidgetContext) -> tuple[str, AnyKeyboard | None]:
        # собираем и возвращаем (текст, клавиатуру)
        ...

    async def handle_callback(self, value: str, ctx: WidgetContext) -> Advance | Reject | NoOp:
        return Advance(value=value, summary=value)

    async def handle_message(self, message: MessageCute, ctx: WidgetContext) -> Advance | Reject | NoOp:
        return Reject(message="Используйте кнопки выше.")
```

Типы результатов обработчиков:

| Тип | Что происходит |
|-----|---------------|
| `Advance(value, summary)` | Сохранить значение, перейти к следующему полю |
| `Stay(new_value)` | Перерисовать виджет с обновлённым состоянием (напр., инкремент счётчика) |
| `Reject(message)` | Показать ошибку, остаться на текущем поле |
| `NoOp()` | Ничего не делать |

`WidgetContext` даёт доступ к `flow_name`, `field_name`, `current_value`, `base_type`, `validators`, `is_optional`, `flow_state` (собранные значения), `dynamic_options` и `theme`.

---

**Назад: [Начало работы](getting-started.md)** | **Далее: [Представления](views.md)**

[Оглавление](readme.md)
