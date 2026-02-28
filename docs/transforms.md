# Flow Transforms

Transforms augment flows with cross-cutting behavior — cancel support, back navigation, progress indicators, and sub-flow stacking. Apply them with `.chain()`:

```python
from teleflow.flow import tg_flow, with_cancel, with_back, with_progress

@derive(tg.flow("register", description="Sign up").chain(
    with_cancel(),
    with_back(),
    with_progress(),
))
@dataclass
class Registration:
    name: Annotated[str, TextInput("Name?")]
    age: Annotated[int, Counter("Age?")]
    ...
```

## with_cancel()

Adds `/cancel` support. At any point during the flow, the user can send `/cancel` to abort. The flow state is cleared and a cancellation message is sent.

```python
@derive(tg.flow("order").chain(with_cancel()))
```

## with_back()

Adds `/back` support. The user can send `/back` to return to the previous field and re-answer it. Navigates backward through prompted fields (skipping `When`-false fields).

```python
@derive(tg.flow("survey").chain(with_back()))
```

## with_progress()

Adds a visual progress indicator to each prompt:

```
████░░░░░░ 4/10

What's your name?
```

```python
@derive(tg.flow("onboarding").chain(with_progress()))
```

## with_summary()

Adds an auto-generated confirmation step after all fields are collected. The user sees a summary of their answers and must confirm before `finish()` is called.

```python
@derive(tg.flow("application").chain(with_summary()))
```

## with_show_mode(mode)

Override the flow's ShowMode:

```python
from teleflow.flow import ShowMode

@derive(tg.flow("wizard").chain(with_show_mode(ShowMode.EDIT)))
```

| Mode | Behavior |
|------|----------|
| `SEND` | New message per prompt (default) |
| `EDIT` | Edit previous message in place |
| `DELETE_AND_SEND` | Delete old + send new |

## with_launch_mode(mode)

Override the flow's LaunchMode — what happens when a user sends the command while already in the flow:

```python
from teleflow.flow import LaunchMode

@derive(tg.flow("quiz").chain(with_launch_mode(LaunchMode.EXCLUSIVE)))
```

| Mode | Behavior |
|------|----------|
| `STANDARD` | Command text treated as field input |
| `RESET` | Restart from scratch |
| `EXCLUSIVE` | Block with "already in progress" |
| `SINGLE_TOP` | Re-send current prompt |

## with_stacking(stack)

Enables sub-flow navigation. A flow can push itself onto a stack and launch another flow. When the sub-flow finishes, the parent resumes.

```python
from teleflow.flow import with_stacking, FlowStack, FinishResult

stack = FlowStack()  # in-memory, or implement FlowStackStorage for persistence

@derive(tg.flow("create_project").chain(with_stacking(stack)))
@dataclass
class CreateProject:
    name: Annotated[str, TextInput("Project name?")]

    async def finish(self) -> Result[FinishResult, DomainError]:
        # Push to stack and start the "invite" flow
        return Ok(FinishResult.sub_flow("Project created! Now invite members.", command="invite"))


@derive(tg.flow("invite").chain(with_stacking(stack)))
@dataclass
class InviteMembers:
    email: Annotated[str, TextInput("Email to invite?")]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message("Invited!"))
        # After this, the parent "create_project" flow resumes
```

Custom storage backend:

```python
from teleflow.flow import FlowStackStorage, StackFrame

class RedisFlowStack:
    async def push(self, key: str, frame: StackFrame) -> None: ...
    async def pop(self, key: str) -> StackFrame | None: ...
```

## Chaining multiple transforms

Transforms compose naturally — order doesn't matter:

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
