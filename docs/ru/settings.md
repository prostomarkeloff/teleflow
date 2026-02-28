# Settings

У каждого бота есть настройки — выбор языка, переключатели уведомлений, значения по умолчанию. Паттерн settings даёт пользователям обзор текущих значений и позволяет редактировать любое поле инлайн, используя те же виджеты, что и в flows.

## Как работают settings

У паттерна два режима. **Режим обзора** показывает все поля как сводку с кнопкой на каждое:

```
Никнейм: Alice
Громкость: 70
Тёмная тема: Вкл

[Никнейм: Alice]  [Громкость: 70]  [Тёмная тема: Вкл]
```

Когда пользователь нажимает кнопку, вид переключается в **режим редактирования** — виджет поля отрисовывается инлайн (текстовый промпт, счётчик, переключатель — всё, что вы аннотировали). После редактирования срабатывает `@on_save`, и вид возвращается к обзору с обновлённым значением.

## Объявление settings

```python
from teleflow.settings import tg_settings, on_save, format_settings
from teleflow.browse import query
from teleflow.flow import TextInput, Counter, Toggle

@derive(tg.settings("config", description="Настройки бота"))
@dataclass
class BotConfig:
    nickname: Annotated[str, TextInput("Новый никнейм:")]
    volume: Annotated[int, Counter("Громкость:", min=0, max=100, step=10)]
    dark_mode: Annotated[bool, Toggle("Тёмная тема:")]

    @classmethod
    @query
    async def fetch(cls, uid: Annotated[int, compose.Node(UserId)],
                    db: ConfigDB) -> BotConfig:
        return await db.get(uid)

    @classmethod
    @on_save
    async def save(cls, settings: BotConfig, uid: Annotated[int, compose.Node(UserId)],
                   db: ConfigDB) -> None:
        await db.update(uid, settings)

    @classmethod
    @format_settings
    def render(cls, s: BotConfig) -> str:
        return f"Никнейм: {s.nickname}\nГромкость: {s.volume}%\nТёмная тема: {'Вкл' if s.dark_mode else 'Выкл'}"
```

Три декоратора, каждый с чёткой ролью:

### @query — загрузка текущих значений

Возвращает датакласс настроек с текущими значениями. Как в browse, поддерживает DI для доступа к базам и текущему пользователю.

```python
@classmethod
@query
async def fetch(cls, uid: Annotated[int, compose.Node(UserId)]) -> BotConfig:
    ...
```

### @on_save — сохранение изменений

Вызывается каждый раз, когда пользователь редактирует поле. Получает полный объект настроек с уже применённым обновлением.

```python
@classmethod
@on_save
async def save(cls, settings: BotConfig, uid: Annotated[int, compose.Node(UserId)]) -> None:
    ...
```

### @format_settings — кастомный обзор

Опционален. Контролирует, что пользователь видит в режиме обзора. Без него teleflow рендерит все поля как `поле: значение`.

```python
@classmethod
@format_settings
def render(cls, s: BotConfig) -> str:
    return f"Никнейм: {s.nickname}\n..."
```

## Параметры

| Параметр | Тип | Значение | Описание |
|----------|-----|----------|----------|
| `command` | `str` | обязателен | Команда Telegram |
| `description` | `str \| None` | `None` | Текст для help |
| `order` | `int` | `100` | Позиция в help |

## Переиспользование виджетов

Ключевой момент: settings переиспользует виджеты из flow. Аннотируйте поле с `TextInput`, `Counter`, `Toggle`, `Inline`, `DatePicker` — любой виджет из [Flows и виджеты](flows.md) работает. При нажатии на поле настроек виджет отрисовывается как инлайн-редактор. Никакой отдельной системы виджетов, никакого дублирования.

---

**Назад: [Представления](views.md)** | **Далее: [Трансформы](transforms.md)**

[Оглавление](readme.md)
