# Theming

Not every bot speaks English. Not every design needs the same icons. teleflow's theming system lets you replace every button label, status indicator, and error message.

## Setting a theme

Pass a `UITheme` to your `TGApp` and it applies everywhere:

```python
from teleflow.uilib.theme import UITheme, NavUI, SelectionUI, ActionUI, DisplayUI, ErrorUI

theme = UITheme(
    nav=NavUI(back="Назад", back_arrow="◀ Назад"),
    action=ActionUI(done="Готово", cancel="Отменено."),
)

tg = TGApp(key_node=UserId, theme=theme)
```

You only need to override what you want to change — everything else keeps its default.

Individual patterns also accept a `theme` parameter if you need per-pattern customization.

## Theme components

`UITheme` is composed of five sub-dataclasses, each responsible for a category of strings.

### NavUI — navigation buttons

Controls pagination and back buttons across browse, dashboard, and flows.

| Field | Default | Used in |
|-------|---------|---------|
| `prev` | `"◀"` | Page arrow |
| `next` | `"▶"` | Page arrow |
| `prev_label` | `"◀️ Prev"` | Full previous button |
| `next_label` | `"Next ▶️"` | Full next button |
| `back` | `"Back"` | Back button text |
| `back_arrow` | `"◀ Back"` | Back button with arrow |

### SelectionUI — selection indicators

Controls how selected/unselected state looks in Radio, Multiselect, Toggle, and filter tabs.

| Field | Default | Used in |
|-------|---------|---------|
| `checked` | `"✅"` | Multiselect selected |
| `unchecked` | `"⬜"` | Multiselect unselected |
| `radio_on` | `"🔘"` | Radio selected |
| `radio_off` | `"⚪"` | Radio unselected |
| `toggle_on` | `"🟢"` | Toggle on |
| `toggle_off` | `"🔴"` | Toggle off |
| `tab_active` | `"🔘"` | Active filter tab |
| `tab_inactive` | `"⚪"` | Inactive filter tab |

### ActionUI — button labels

Controls the text on action buttons across all patterns.

| Field | Default | Used in |
|-------|---------|---------|
| `done` | `"Done ✓"` | Done/confirm button |
| `ok` | `"OK"` | OK button |
| `yes` | `"Yes"` | Confirm dialog yes |
| `no` | `"No"` | Confirm dialog no |
| `cancel` | `"Cancelled."` | Cancel message |
| `remove_last` | `"Remove last"` | ListBuilder |
| `decrement` | `"−"` | Counter minus |
| `increment` | `"+"` | Counter plus |

### DisplayUI — value formatting

Controls how values are displayed in settings overview, summaries, and pagination.

| Field | Default | Used in |
|-------|---------|---------|
| `none_value` | `"(not set)"` | Unset fields |
| `bool_true` | `"Yes"` | Boolean true |
| `bool_false` | `"No"` | Boolean false |
| `no_options` | `"(no options available)"` | Empty dynamic options |
| `entity_not_found` | `"Entity not found."` | Missing entity in browse |
| `disabled_date` | `"·"` | Disabled date in DatePicker |
| `date_format` | `"%b %d, %Y"` | Date display |
| `page_format` | `"{}/{}"` | Page counter (e.g., "1/5") |

### ErrorUI — error and validation messages

Every error message the user can see is configurable. Format strings use `{}` for dynamic values.

| Field | Default | Used in |
|-------|---------|---------|
| `use_buttons` | `"Please use the buttons above."` | Wrong input type (multiple buttons) |
| `use_button` | `"Please use the button above."` | Wrong input type (single button) |
| `send_text` | `"Please send a text message."` | TextInput |
| `send_photo` | `"Please send a photo."` | PhotoInput |
| `send_document` | `"Please send a document."` | DocumentInput |
| `send_video` | `"Please send a video."` | VideoInput |
| `send_voice` | `"Please send a voice message."` | VoiceInput |
| `send_location` | `"Please share a location."` | LocationInput |
| `send_contact` | `"Please use the Share Contact button."` | ContactInput |
| `send_number` | `"Please enter a number."` | NumberInput |
| `send_media` | `"Please send a photo, document, or video."` | MediaGroupInput |
| `use_calendar` | `"Please use the calendar buttons above."` | DatePicker |
| `use_time_picker` | `"Please use the time picker buttons above."` | TimePicker |
| `use_slider` | `"Please use the slider buttons above."` | Slider |
| `enter_pin` | `"Please enter all digits first."` | PinInput |
| `select_option` | `"Please select an option first."` | Radio/Inline |
| `select_rating` | `"Please select a rating first."` | Rating |
| `select_days` | `"Please select at least one day."` | RecurrencePicker |
| `too_short` | `"Too short (min {} chars)"` | MinLen validation |
| `too_long` | `"Too long (max {} chars)"` | MaxLen validation |
| `invalid_format` | `"Invalid format (expected {})"` | Pattern validation |
| `range_error` | `"Must be between {} and {}."` | Number range |
| `min_select` | `"Select at least {}"` | Multiselect min |
| `max_items` | `"Max {} items"` | ListBuilder/MediaGroup max |
| `max_reached` | `"Maximum {} items reached. Press Done."` | ListBuilder limit hit |
| `min_required` | `"Please add at least {} items."` | ListBuilder/MediaGroup min |

## Example: Russian theme

A full localization — override navigation, actions, display labels, and common errors:

```python
ru_theme = UITheme(
    nav=NavUI(
        prev_label="◀️ Назад",
        next_label="Вперед ▶️",
        back="Назад",
        back_arrow="◀ Назад",
    ),
    action=ActionUI(
        done="Готово ✓",
        ok="ОК",
        yes="Да",
        no="Нет",
        cancel="Отменено.",
        remove_last="Удалить последний",
        decrement="−",
        increment="+",
    ),
    display=DisplayUI(
        none_value="(не задано)",
        bool_true="Да",
        bool_false="Нет",
        no_options="(нет вариантов)",
        date_format="%d.%m.%Y",
        entity_not_found="Не найдено.",
    ),
    errors=ErrorUI(
        use_buttons="Используйте кнопки выше.",
        use_button="Используйте кнопку выше.",
        send_text="Отправьте текстовое сообщение.",
        send_photo="Отправьте фотографию.",
        send_number="Введите число.",
        too_short="Слишком коротко (мин. {} символов)",
        too_long="Слишком длинно (макс. {} символов)",
        select_option="Сначала выберите вариант.",
    ),
)

tg = TGApp(key_node=UserId, theme=ru_theme)
```

---

**Prev: [Transforms](transforms.md)**

[Docs index](readme.md)
