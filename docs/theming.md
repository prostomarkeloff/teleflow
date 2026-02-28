# Theming

Every string and icon in teleflow is configurable through `UITheme`. Pass a custom theme to `TGApp` or to individual patterns.

## UITheme

```python
from teleflow.uilib.theme import UITheme, NavUI, SelectionUI, ActionUI, DisplayUI, ErrorUI

theme = UITheme(
    nav=NavUI(...),
    selection=SelectionUI(...),
    action=ActionUI(...),
    display=DisplayUI(...),
    errors=ErrorUI(...),
)

tg = TGApp(key_node=UserId, theme=theme)
```

## Sub-components

### NavUI — navigation buttons

| Field | Default | Description |
|-------|---------|-------------|
| `prev` | `"◀"` | Previous page arrow |
| `next` | `"▶"` | Next page arrow |
| `prev_label` | `"◀️ Prev"` | Previous button label |
| `next_label` | `"Next ▶️"` | Next button label |
| `back` | `"Back"` | Back button text |
| `back_arrow` | `"← Back"` | Back button with arrow |

### SelectionUI — selection state indicators

| Field | Default | Description |
|-------|---------|-------------|
| `checked` | `"✅"` | Selected item (multiselect) |
| `unchecked` | `"⬜"` | Unselected item (multiselect) |
| `radio_on` | `"🔘"` | Selected option (radio) |
| `radio_off` | `"⭕"` | Unselected option (radio) |
| `toggle_on` | `"🟢"` | Toggle on state |
| `toggle_off` | `"🔴"` | Toggle off state |
| `tab_active` | active indicator | Active filter tab |
| `tab_inactive` | inactive indicator | Inactive filter tab |

### ActionUI — button labels

| Field | Default | Description |
|-------|---------|-------------|
| `done` | `"Done"` | Done/confirm button |
| `ok` | `"OK"` | OK button |
| `yes` | `"Yes"` | Yes (confirm dialog) |
| `no` | `"No"` | No (confirm dialog) |
| `cancel` | `"Cancelled."` | Cancellation message |
| `remove_last` | `"Remove last"` | ListBuilder remove |
| `decrement` | `"−"` | Counter decrement |
| `increment` | `"+"` | Counter increment |

### DisplayUI — formatting

| Field | Default | Description |
|-------|---------|-------------|
| `none_value` | `"(not set)"` | Display for None values |
| `bool_true` | `"Yes"` | Boolean true display |
| `bool_false` | `"No"` | Boolean false display |
| `no_options` | `"(no options available)"` | Empty dynamic options |
| `date_format` | `"%b %d, %Y"` | Date formatting |
| `page_format` | `"{}/{}"` | Page counter format |

### ErrorUI — error and validation messages

| Field | Default | Description |
|-------|---------|-------------|
| `use_buttons` | `"Please use the button(s) above"` | Wrong input type |
| `send_text` | `"Please send a text message"` | Expected text |
| `send_photo` | `"Please send a photo"` | Expected photo |
| `send_document` | `"Please send a document"` | Expected document |
| `too_short` | min length error | MinLen validation |
| `too_long` | max length error | MaxLen validation |
| `select_option` | `"Please select an option"` | No option selected |
| `min_select` | min selection error | Multiselect minimum |
| `max_items` | max items error | ListBuilder/MediaGroup max |

## Example: Russian theme

```python
ru_theme = UITheme(
    nav=NavUI(
        prev_label="◀️ Назад",
        next_label="Вперед ▶️",
        back="Назад",
        back_arrow="← Назад",
    ),
    action=ActionUI(
        done="Готово",
        ok="ОК",
        yes="Да",
        no="Нет",
        cancel="Отменено.",
    ),
    display=DisplayUI(
        none_value="(не задано)",
        bool_true="Да",
        bool_false="Нет",
        no_options="(нет вариантов)",
        date_format="%d.%m.%Y",
    ),
    errors=ErrorUI(
        use_buttons="Используйте кнопки выше",
        send_text="Отправьте текстовое сообщение",
    ),
)
```
