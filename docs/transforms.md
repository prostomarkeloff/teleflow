# Transforms

A bare flow works, but real users expect more — a way to cancel, go back to a previous question, see how far they've gotten. Transforms add these behaviors without touching your flow logic.

Apply transforms with `.chain()`:

```python
from teleflow.flow import with_cancel, with_back, with_progress

@derive(tg.flow("register", description="Sign up").chain(
    with_cancel(),
    with_back(),
    with_progress(),
))
@dataclass
class Registration:
    ...
```

Each transform wraps the flow with additional handling. They compose freely — order doesn't matter, and you can stack as many as you need.

## with_cancel()

The most important transform. Lets the user send `/cancel` at any point to abort the flow. State is cleared and a cancellation message is sent.

```python
@derive(tg.flow("order").chain(with_cancel()))
```

Without this, a user stuck in a flow has no way out except waiting for the session to expire.

## with_back()

Adds `/back` support. The user sends `/back` and returns to the previous field to re-answer it. Navigation is smart — it skips over `When`-conditional fields that were hidden.

```python
@derive(tg.flow("survey").chain(with_back()))
```

Pairs well with `with_cancel()` for a complete navigation experience.

## with_progress()

Shows a visual progress bar above each prompt:

```
████░░░░░░ 4/10

What's your name?
```

Helpful for long flows so users know how much is left.

```python
@derive(tg.flow("onboarding").chain(with_progress()))
```

## with_summary()

Adds an automatic confirmation step after all fields are collected. The user sees a summary of their answers and must confirm before `finish()` runs. If they reject, the flow restarts.

```python
@derive(tg.flow("application").chain(with_summary()))
```

## with_show_mode(mode) and with_launch_mode(mode)

Override the flow's `ShowMode` or `LaunchMode` via transform instead of setting it in the pattern declaration. Useful when the same pattern class is reused with different modes:

```python
from teleflow.flow import ShowMode, LaunchMode

@derive(tg.flow("wizard").chain(
    with_show_mode(ShowMode.EDIT),
    with_launch_mode(LaunchMode.EXCLUSIVE),
))
```

See [Flows & Widgets](flows.md) for what each mode does.

## with_stacking(stack)

This is the most powerful transform. It enables sub-flow navigation — one flow can pause itself, launch another flow, and resume when the child finishes.

```python
from teleflow.flow import with_stacking, FlowStack, FinishResult

stack = FlowStack()  # in-memory; implement FlowStackStorage for persistence

@derive(tg.flow("create_project").chain(with_stacking(stack)))
@dataclass
class CreateProject:
    name: Annotated[str, TextInput("Project name?")]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.sub_flow(
            "Project created! Now invite members.",
            command="invite",
        ))


@derive(tg.flow("invite").chain(with_stacking(stack)))
@dataclass
class InviteMembers:
    email: Annotated[str, TextInput("Email to invite?")]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message("Invited!"))
        # parent "create_project" flow resumes automatically
```

Both flows must share the same `FlowStack` instance and both must have `with_stacking()` applied.

`FinishResult.sub_flow(text, command="child")` pushes the current flow to the stack and starts the child. When the child calls `FinishResult.message(...)`, the stack pops and the parent continues.

For production, implement `FlowStackStorage` to persist the stack (e.g., in Redis):

```python
from teleflow.flow import FlowStackStorage, StackFrame

class RedisFlowStack:
    async def push(self, key: str, frame: StackFrame) -> None: ...
    async def pop(self, key: str) -> StackFrame | None: ...
```

## Putting it all together

A fully equipped flow:

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
    name: Annotated[str, TextInput("Name?")]
    email: Annotated[str, TextInput("Email?"), Pattern(r"^[\w.]+@[\w.]+$")]
    plan: Annotated[str, Inline("Plan:", free="Free", pro="Pro")]

    async def finish(self) -> Result[FinishResult, DomainError]:
        return Ok(FinishResult.message(f"Welcome, {self.name}!"))
```

This flow has: cancel support, back navigation, a progress bar, a confirmation summary, clean message editing, and the ability to launch sub-flows. All from six transform calls.

---

**Prev: [Settings](settings.md)** | **Next: [Theming](theming.md)**

[Docs index](readme.md)
