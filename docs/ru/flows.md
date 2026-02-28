# Flows и виджеты

Flow — это многошаговый диалог. Пользователь отправляет `/command`, бот задаёт вопросы по очереди, собирает ответы в типизированный датакласс и вызывает `finish()`.

## Объявление flow

```python
from teleflow.flow import tg_flow, TextInput, Inline

@derive(tg_flow(
    command="order",
    key_node=UserId,
    description="Оформить заказ",
))
@dataclass
class Order:
    item: Annotated[str, Inline("Выберите:", pizza="Пицца", burger="Бургер")]
    note: Annotated[str, TextInput("Пожелания к заказу?")]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message(f"Заказ: {self.item}!"))
```

### Параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `command` | `str` | обязателен | Команда Telegram (`"start"` → `/start`) |
| `key_node` | `type` | обязателен | nodnod-нода для маршрутизации сессий |
| `*caps` | `SurfaceCapability` | `()` | Дополнительные capabilities |
| `description` | `str \| None` | `None` | Текст для `/help` |
| `order` | `int` | `100` | Порядок сортировки в help |
| `show_mode` | `ShowMode` | `SEND` | Как рендерятся промпты |
| `launch_mode` | `LaunchMode` | `STANDARD` | Поведение при повторном входе |
| `theme` | `UITheme` | default | Строки и иконки UI |

При использовании `TGApp` предпочтительнее `tg.flow(...)` вместо `tg_flow(...)` напрямую — он наследует key_node, тему и валидирует уникальность команд.

## Виджеты

Каждое поле датакласса аннотируется виджетом, который определяет способ сбора значения.

### Базовый ввод

**TextInput(prompt)** — текстовое сообщение.

```python
name: Annotated[str, TextInput("Как вас зовут?")]
```

**NumberInput(prompt, min, max, shortcuts)** — число. Опционально — кнопки быстрого выбора.

```python
amount: Annotated[int, NumberInput("Сколько?", min=1, max=100, shortcuts=(5, 10, 25))]
```

**Confirm(prompt, yes_label, no_label)** — вопрос Да/Нет. Результат — `bool`.

```python
agree: Annotated[bool, Confirm("Принимаете условия?")]
```

### Выбор

**Inline(prompt, columns, \*\*options)** — одиночный выбор через inline-клавиатуру. Быстрый, без состояния.

```python
color: Annotated[str, Inline("Цвет:", red="Красный", blue="Синий", green="Зелёный")]
```

**Radio(prompt, columns, \*\*options)** — одиночный выбор с видимым состоянием и кнопкой «Готово».

```python
size: Annotated[str, Radio("Размер:", s="S", m="M", l="L", xl="XL")]
```

**Multiselect(prompt, columns, min_selected, max_selected, \*\*options)** — множественный выбор с галочками.

```python
toppings: Annotated[str, Multiselect(
    "Топпинги:",
    cheese="Сыр", mushrooms="Грибы", peppers="Перец",
    min_selected=1, max_selected=3,
)]
```

**ScrollingInline(prompt, columns, page_size, \*\*options)** — постраничный inline для большого числа вариантов.

**EnumInline(prompt, columns)** — автогенерация из Python Enum.

```python
class Priority(enum.Enum):
    LOW = "Низкий"
    MEDIUM = "Средний"
    HIGH = "Высокий"

priority: Annotated[Priority, EnumInline("Приоритет:")]
```

### Интерактивные

**Counter(prompt, min, max, step, default)** — счётчик +/- для целых чисел.

```python
quantity: Annotated[int, Counter("Количество:", min=1, max=99, step=1, default=1)]
```

**Toggle(prompt, on, off)** — переключатель boolean.

```python
notifications: Annotated[bool, Toggle("Уведомления:", on="Вкл", off="Выкл")]
```

**Slider(prompt, min, max, step, big_step, default, presets, filled, empty)** — визуальный слайдер с прогресс-баром.

```python
volume: Annotated[int, Slider("Громкость:", min=0, max=100, step=5, big_step=20)]
```

**Rating(prompt, max_stars, filled, empty)** — рейтинг звёздами.

```python
score: Annotated[int, Rating("Оцените нас:", max_stars=5)]
```

**ListBuilder(prompt, min, max)** — сбор списка текстовых элементов по одному.

```python
tags: Annotated[str, ListBuilder("Добавьте теги (по одному):", min=1, max=10)]
```

**PinInput(prompt, length, mask, secret)** — ввод PIN через нампад.

```python
pin: Annotated[str, PinInput("Введите PIN:", length=4, secret=True)]
```

### Дата и время

**DatePicker(prompt, min_date, max_date)** — календарь с навигацией по месяцам/годам.

```python
birthday: Annotated[str, DatePicker("Дата рождения:", max_date=date.today())]
```

**TimePicker(prompt, min_hour, max_hour, step_minutes)** — выбор часа и минут.

```python
alarm: Annotated[str, TimePicker("Время будильника:", min_hour=6, max_hour=22, step_minutes=15)]
```

**TimeSlotPicker(prompt, columns, date_format)** — временные слоты, сгруппированные по дате (из `@options`).

**RecurrencePicker(prompt, min_hour, max_hour, step_minutes)** — выбор дней недели + время. Результат: `"0,2,4@10:30"`.

### Медиа

Все медиа-виджеты собирают `file_id` (кроме LocationInput — `(lat, lon)`).

```python
photo: Annotated[str, PhotoInput("Отправьте фото:")]
doc: Annotated[str, DocumentInput("Загрузите документ:")]
video: Annotated[str, VideoInput("Отправьте видео:")]
voice: Annotated[str, VoiceInput("Запишите голосовое:")]
location: Annotated[str, LocationInput("Отправьте геолокацию:")]
contact: Annotated[str, ContactInput("Поделитесь контактом:", button_text="Отправить контакт")]
```

**MediaGroupInput(prompt, min, max, accept)** — сбор нескольких медиафайлов.

```python
photos: Annotated[str, MediaGroupInput("Отправьте фото:", min=1, max=5, accept="photo")]
```

### Условные и обзорные

**Prefilled()** — предзаполнено из контекста, не спрашивается.

```python
user_id: Annotated[int, Prefilled()]
```

**Case(selector, \*\*options)** — разный текст в зависимости от значения предыдущего поля.

```python
kind: Annotated[str, Inline("Тип:", bug="Баг", feature="Фича")]
details: Annotated[str, Case(selector="kind", bug="Опишите баг:", feature="Опишите фичу:")]
```

**SummaryReview(\*\*labels)** — показать все собранные значения для подтверждения.

### Динамические опции

Используйте `@options("field_name")` для загрузки вариантов во время выполнения:

```python
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

Динамические виджеты: `DynamicInline`, `DynamicRadio`, `DynamicMultiselect`.

## Завершение flow

Каждая flow-сущность должна иметь метод `finish()`:

```python
async def finish(self) -> Result[FinishResult, DomainError]:
    ...
```

Варианты `FinishResult`:

```python
FinishResult.message("Готово!")                          # текстовый ответ
FinishResult.then("Создано!", command="tasks")           # текст + редирект
FinishResult.sub_flow("Запускаю...", command="invite")   # текст + вложенный flow
FinishResult.with_keyboard("Выберите:", markup)          # текст + клавиатура
```

## Валидация

```python
from teleflow.flow import MinLen, MaxLen, Pattern

username: Annotated[str, TextInput("Логин:"), MinLen(3), MaxLen(20)]
email: Annotated[str, TextInput("Email:"), Pattern(r"^[\w.]+@[\w.]+$")]
```

При невалидном вводе пользователь видит ошибку и повторный запрос.

## Условные поля

```python
from teleflow.flow import When

kind: Annotated[str, Inline("Тип:", bug="Баг", feature="Фича")]
severity: Annotated[str, Inline("Критичность:", high="Высокая", low="Низкая"),
    When(lambda v: v.get("kind") == "bug")]
```

`severity` спрашивается только когда `kind == "bug"`.

## ShowMode

| Режим | Поведение |
|-------|-----------|
| `ShowMode.SEND` | Новое сообщение на каждый промпт (по умолчанию) |
| `ShowMode.EDIT` | Редактирование предыдущего сообщения |
| `ShowMode.DELETE_AND_SEND` | Удаление старого + отправка нового |

## LaunchMode

| Режим | Поведение |
|-------|-----------|
| `LaunchMode.STANDARD` | Текст команды как ввод поля |
| `LaunchMode.RESET` | Перезапуск flow |
| `LaunchMode.EXCLUSIVE` | Блокировка — «уже запущено» |
| `LaunchMode.SINGLE_TOP` | Повторная отправка текущего промпта |

## Кастомные виджеты

Реализуйте протокол `FlowWidget`:

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
        return True

    async def render(self, ctx: WidgetContext) -> tuple[str, AnyKeyboard | None]:
        kb = InlineKeyboard()
        # ... строим клавиатуру
        return self._prompt, kb

    async def handle_callback(self, value: str, ctx: WidgetContext) -> Advance | Stay | Reject | NoOp:
        return Advance(value=value, summary=value)

    async def handle_message(self, message: MessageCute, ctx: WidgetContext) -> Advance | Stay | Reject | NoOp:
        return Reject(message="Используйте кнопки выше.")
```

| Тип | Значение |
|-----|----------|
| `Advance(value, summary)` | Сохранить значение, перейти к следующему полю |
| `Stay(new_value)` | Перерисовать виджет (напр. инкремент счётчика) |
| `Reject(message)` | Показать ошибку, остаться на текущем поле |
| `NoOp()` | Ничего не делать |
