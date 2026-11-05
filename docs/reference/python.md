# Python: files and cleanup

A context manager closes the file when the block ends, including when an
exception leaves it.

```python
from pathlib import Path


def read_names(path: Path) -> list[str]:
    with path.open(encoding="utf-8") as source:
        return [line.strip() for line in source if line.strip()]


if __name__ == "__main__":
    for name in read_names(Path("names.txt")):
        print(name)
```

**DOCS → PYTHON LIBRARY** accepts module names such as `pathlib`, `json`,
`contextlib` and `asyncio`. It opens the downloaded Python manual as text, with
indented examples preserved. Reading it does not import or execute the module.

For an already prepared project, run
`uv run --offline --no-sync --no-managed-python example.py`. This needs its virtual
environment and dependencies to exist first. The offline documentation does not
replace a dependency cache.
