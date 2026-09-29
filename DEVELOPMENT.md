# Development

Notes specific to **zLMDB**: development setup, running the tests, supported runtimes, and release
versioning. The contribution workflow shared by all WAMP projects — GitHub issue first, red → green
tests, and the AI-assistance disclosure — is in [CONTRIBUTING.md](CONTRIBUTING.md).

## Reporting bugs

In addition to what CONTRIBUTING.md asks for, please include:

- the zLMDB version: `python -c "import zlmdb; print(zlmdb.__version__)"`
- the LMDB version, if relevant

## Development setup

Development is driven by [`just`](https://github.com/casey/just) and [`uv`](https://github.com/astral-sh/uv);
run `just` to list all recipes. Every recipe takes the name of a managed virtual environment:
`cpy314`, `cpy313`, `cpy312`, `cpy311` (CPython) or `pypy311` (PyPy).

zLMDB vendors LMDB and FlatBuffers as git submodules, so clone recursively:

```bash
git clone https://github.com/crossbario/zlmdb.git
cd zlmdb
git submodule update --init --recursive
just create cpy314
just install-dev cpy314
```

## Running the tests

```bash
just test cpy314            # the test suite
just test pypy311           # the same on PyPy
just check cpy314           # formatting, typing and the other checks
```

**Supported runtimes:** CPython 3.11–3.14 and PyPy 3.11.

The vendored FlatBuffers runtime is kept in lock-step with Autobahn|Python's (both are used together
by Crossbar.io); change the two together.

## Code style

`ruff` enforces formatting and linting (`just check-format cpy314`); the line length is 88. Add
docstrings for public APIs, and type hints for new code (`just check-typing cpy314`).

## Documentation

The documentation is reStructuredText, built with Sphinx: `just docs cpy314`.

## Versioning

This project uses [CalVer](https://calver.org/) with PEP 440 development releases:
`YY.M.PATCH[.devN]` — for example, `26.7.1` for a stable release and `26.7.1.dev1` while in
development. Between releases the working tree always carries a `.devN` suffix.

The version is stored in two files kept in sync — `pyproject.toml` and `src/zlmdb/_version.py` — and
managed with `just`:

- `just file-version` — show the current version (from both files)
- `just bump-dev` — bump to the next dev version for the current month (`YY.M.1.dev1`)
- `just bump-next 26.7.2.dev1` — set a specific next dev version
- `just prep-release` — strip the `.devN` suffix to cut a stable release

Git tags and releases are created by maintainers only.
