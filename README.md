# `service-common`

Shared utilities intended to be reused across Maco FastAPI microservices.

## Install (from source)

Editable install (recommended for local development):

```bash
pip install -e .
```

Build a wheel:

```bash
python -m build
```

## Usage

### Trace ID middleware + logging

```python
from fastapi import FastAPI

from service_common import configure_logging, register_trace_id_middleware

app = FastAPI()

configure_logging("INFO")
register_trace_id_middleware(app)
```

### Retry helper for upstream calls

```python
from service_common import retry_async


async def fetch_something() -> str:
    # ... your async upstream call ...
    return "ok"


result = await retry_async(
    fetch_something,
    operation_name="fetch_something",
    attempts=3,
    interval_seconds=0.5,
    testing=False,
)
```

### Consistent internal error responses

```python
from service_common import internal_server_error_response, log_error_code_with_stack


try:
    raise RuntimeError("boom")
except Exception as exc:
    code = log_error_code_with_stack(exc)
    response = internal_server_error_response(code=code)
```

