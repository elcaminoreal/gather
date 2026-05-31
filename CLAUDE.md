# gather Development Guidelines

## Verifying Your Work

`nox` is the single source of truth for whether a change is correct. A
change is "done" only when the full `nox` run reports every session
successful and exits `0`. Treat that exit code as the definition of done.

Follow this process for every change:

1. **Provide the interpreters nox asks for.** The sessions pin specific
   Python versions (see `VERSIONS` in `noxfile.py`, currently 3.12, 3.13,
   3.14, plus the `dry_release` interpreter). Install each one so nox runs
   the session instead of skipping it. With [`uv`](https://docs.astral.sh/uv/):

   ```bash
   uv python install 3.12 3.13 3.14
   ```

   Put each interpreter on `PATH` (e.g. symlink `uv python find 3.14` to
   `python3.14`) so nox's discovery finds it. A *skipped* session is an
   unverified session; arrange for every session to actually execute.

2. **Run the whole suite and read the summary.**

   ```bash
   nox
   ```

   Confirm the trailing summary shows `success` for every session —
   `lint`, `tests-3.12`, `tests-3.13`, `tests-3.14`, `mypy`, `docs`, and
   `dry_release` — and that the process exit code is `0`.

3. **Iterate against nox itself.** When fixing one session, re-run that
   session (`nox -s lint`, `nox -s mypy`, `nox -s tests-3.14`) and read its
   real output to choose the next edit. Let the tool's report drive each
   change. For fast inner loops you may run a tool from the session's
   prepared virtualenv under `build/nox/<session>/bin/`, but always
   re-confirm with `nox` before considering the work complete.

4. **Confirm the full suite is green on a clean tree before committing,
   and again before pushing.** Make the commit/push reflect a state you
   have just observed nox accept end-to-end. Have the verified `nox`
   summary in hand when you state that the work passes.

### Suppressing a specific finding

When a `stolid` finding is genuinely the intended design (e.g. venusian
requires separate top-level decorated definitions, or a Protocol
deliberately mirrors a wide stdlib signature), suppress that one code with
a `# noqa: CODE` comment placed **on the exact line stolid reports** (run
the session to see the reported line and column). Keep the waiver narrow —
name the single code — and leave the rest of the rules in force.

## Running Tests and Linting

Use `nox` to run all checks. If nox is not installed:

```bash
pip install nox
```

Run all checks:
```bash
nox
```

Run specific sessions:
```bash
nox -s tests    # Run tests with coverage
nox -s lint     # Run black and stolid
nox -s mypy     # Run type checking
```

## Testing Framework: Virtue

This project uses **Virtue** as the test runner, not pytest. Tests are standard `unittest.TestCase` classes with methods prefixed with `test_`. Use **PyHamcrest** matchers for readable assertions.

Example test pattern:

```python
import unittest
from hamcrest import assert_that, equal_to

class TestPlanStack(unittest.TestCase):
    def test_add_step(self) -> None:
        plan = PlanStack()
        result = plan.add("Do something")
        assert_that(plan.current_plan(), equal_to(["Do something"]))
```

## No Mocking - Dependency Injection Only

Tests **never** use `unittest.mock.patch`. All dependencies are injected.

Bad:
```python
from unittest.mock import patch

class TestBad(unittest.TestCase):
    @patch("mymodule.requests.get")
    def test_fetch(self, mock_get):
        mock_get.return_value.json.return_value = {"data": 1}
        result = fetch_data()
        assert_that(result, equal_to(1))
```

Good:
```python
class TestGood(unittest.TestCase):
    def test_fetch(self) -> None:
        fake_client = FakeHTTPClient(response={"data": 1})
        fetcher = DataFetcher(client=fake_client)
        result = fetcher.fetch()
        assert_that(result, equal_to(1))
```

This makes tests deterministic and easier to reason about.

## 100% Code Coverage Required

The project enforces 100% code coverage with branch coverage. Any untested code must be explicitly marked:

```python
if rare_edge_case:  # pragma: no cover
    handle_edge_case()
```

Use `# pragma: no cover` sparingly and only when testing is genuinely impractical.

## Object-Oriented Design Principles

### Declare Interfaces with Protocol

Make contracts explicit using `typing.Protocol`:

```python
from typing import Protocol

class HTTPClient(Protocol):
    def get(self, url: str) -> Response: ...
    def post(self, url: str, data: bytes) -> Response: ...

class DataFetcher:
    def __init__(self, client: HTTPClient) -> None:
        self.client = client
```

This enables:
- Clear communication of expected behavior
- Easy creation of test doubles
- Type checker verification of implementations

### Simplify Initialization

Keep constructors boring - only assign parameters to attributes:

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True, kw_only=True)
class DataProcessor:
    client: HTTPClient
    config: Config

    @classmethod
    def from_environment(cls) -> "DataProcessor":
        # Complex setup logic goes in class methods
        return cls(
            client=RealHTTPClient(),
            config=Config.load(),
        )
```

Never do I/O or complex object creation in `__init__`.

### Avoid Mutation

Prefer immutable objects using `@dataclass(frozen=True)`:

```python
from dataclasses import dataclass, replace

@dataclass(frozen=True, slots=True)
class Settings:
    timeout: int
    retries: int

# Create modified copies instead of mutating
new_settings = replace(settings, timeout=30)
```

### Avoid Hiding

Don't use private methods that duplicate logic. Extract into separate classes:

Bad:
```python
class Processor:
    def _validate(self, data):
        # validation logic

    def process_a(self, data):
        self._validate(data)
        # process A

    def process_b(self, data):
        self._validate(data)
        # process B
```

Good:
```python
class Validator:
    def validate(self, data):
        # validation logic

class Processor:
    def __init__(self, validator: Validator) -> None:
        self.validator = validator
```

### Avoid Inheritance

Use composition and Protocol instead of inheritance:

Bad:
```python
class BaseHandler:
    def handle(self):
        self.validate()
        self.process()

class MyHandler(BaseHandler):
    def validate(self): ...
    def process(self): ...
```

Good:
```python
from dataclasses import dataclass

class Validator(Protocol):
    def validate(self, data: Data) -> None: ...

class Processor(Protocol):
    def process(self, data: Data) -> Result: ...

@dataclass(frozen=True, slots=True)
class Handler:
    validator: Validator
    processor: Processor

    def handle(self, data: Data) -> Result:
        self.validator.validate(data)
        return self.processor.process(data)
```

### Keep Methods Minimal

Classes should be data containers with minimal behavior. Prefer module-level functions or `functools.singledispatch` for complex operations:

```python
import functools

@functools.singledispatch
def serialize(obj) -> bytes:
    raise TypeError(f"Cannot serialize {type(obj)}")

@serialize.register
def _(obj: User) -> bytes:
    return json.dumps({"name": obj.name}).encode()

@serialize.register
def _(obj: Order) -> bytes:
    return json.dumps({"items": obj.items}).encode()
```
