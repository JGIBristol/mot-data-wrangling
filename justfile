# We prepend most commands with `uv run` to ensure we are
# running inside the Python virtual environment

[private]
default:
    @just --list --unsorted

# Run format, checks and tests
all: format check test

# Format using ruff
format:
    uv run ruff format

# Lint using ruff and check types using mypy
check:
    uv run ruff check --fix
    uv run mypy src/

# Run pytest
test:
    uv run pytest
