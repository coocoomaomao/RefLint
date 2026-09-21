# Contributing

Thanks for helping improve RefLint.

## Development

~~~bash
python -m venv .venv
pip install -e ".[dev]"
pytest
~~~

When adding a rule:

- prefer deterministic checks over guesses,
- add a focused fixture/test,
- explain false-positive risks,
- keep network-backed verification separate from local syntax/consistency checks.
