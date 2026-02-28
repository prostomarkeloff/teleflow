# Settings

`tg_settings()` генерирует панель настроек, где пользователи нажимают на поля для инлайн-редактирования через виджеты flow.

## Объявление настроек

```python
from teleflow.settings import tg_settings, on_save, format_settings
from teleflow.flow import TextInput, Counter, Toggle

@derive(tg.settings("config", description="Настройки бота"))
@dataclass
class BotConfig:
    nickname: Annotated[str, TextInput("Новый никнейм:")]
    volume: Annotated[int, Counter("Громкость:", min=0, max=100, step=10)]
    dark_mode: Annotated[bool, Toggle("Тёмная тема:")]

    @classmethod
    @query
    async def fetch(cls, uid: UserId, db: ConfigDB) -> BotConfig:
        return await db.get(uid.value)

    @classmethod
    @on_save
    async def save(cls, settings: BotConfig, uid: UserId, db: ConfigDB) -> None:
        await db.update(uid.value, settings)
```

При отправке `/config` пользователь видит обзор текущих значений с кнопкой на каждое поле. Нажатие открывает соответствующий виджет. После редактирования вызывается `@on_save`.

## Как это работает

У паттерна settings два режима:

**Обзорный режим** — показывает все поля как кнопки:
```
Никнейм: Alice
Громкость: 70
Тёмная тема: Вкл

[Никнейм: Alice]  [Громкость: 70]  [Тёмная тема: Вкл]
```

**Режим редактирования** — рендерит виджет поля:
```
Громкость:
   ← 70 →
[Готово]  [Назад]
```

Кнопка «Назад» возвращает к обзору. Завершение редактирования вызывает `@on_save` и возвращает к обзору с обновлённым значением.

## Декораторы

### @query

Загружает текущие настройки. Возвращает экземпляр датакласса.

```python
@classmethod
@query
async def fetch(cls, uid: UserId, db: ConfigDB) -> BotConfig:
    return await db.get(uid.value)
```

### @on_save

Вызывается после редактирования поля. Получает полный объект настроек с обновлённым полем.

```python
@classmethod
@on_save
async def save(cls, settings: BotConfig, uid: UserId, db: ConfigDB) -> None:
    await db.update(uid.value, settings)
```

### @format_settings

Опциональный кастомный рендерер обзора.

```python
@classmethod
@format_settings
def render(cls, s: BotConfig) -> str:
    return f"Никнейм: {s.nickname}\nГромкость: {s.volume}%"
```

## Параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|-------------|----------|
| `command` | `str` | обязателен | Команда Telegram |
| `key_node` | `type` | обязателен | nodnod-нода для маршрутизации |
| `*caps` | `SurfaceCapability` | `()` | Дополнительные capabilities |
| `description` | `str \| None` | `None` | Текст для help |
| `order` | `int` | `100` | Порядок в help |
| `theme` | `UITheme` | default | Настройка UI |

## Переиспользование виджетов

Settings переиспользует те же виджеты, что и flows. Любой виджет из flow-аннотации работает в settings — TextInput, Counter, Toggle, Inline, Multiselect, DatePicker и т.д.
