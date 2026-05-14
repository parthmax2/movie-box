# Contributing

Thanks for helping improve movie-box.

## Local Setup

```sh
python -m venv venv
venv\Scripts\activate
python -m pip install -e ".[cli]" pytest pytest-asyncio coverage
```

## Checks

Run these before opening a pull request:

```sh
python -m compileall -q src tests
python -m pytest --collect-only -q -p no:cacheprovider
python -m pytest -q -p no:cacheprovider tests\v1\cli\test_commands.py::test_version tests\v2\cli\test_commands.py::test_version tests\v3\cli\test_commands.py::test_version
```

Some tests make live HTTP requests and can fail when upstream hosts are blocked
or unavailable. Keep new tests deterministic where possible.

## Pull Requests

- Keep changes focused.
- Add or update tests for behavior changes.
- Update README or docs when user-facing behavior changes.
- Do not commit local virtual environments, caches, downloaded media, or secrets.
