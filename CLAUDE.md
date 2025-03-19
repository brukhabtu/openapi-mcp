# CLAUDE.md - OpenAPI-MCP Project Guide

## Build & Environment Commands
- Setup: `uv venv && source .venv/bin/activate && uv pip install -e ".[dev]"`
- Install dependencies: `uv pip install -e ".[dev]"`
- Run CLI: `uv run python -m openapi_mcp.cli` or `uv run openapi-mcp`
- Build package: `uv run python -m build`

## Testing
- Run all tests: `uv run pytest`
- Run specific test: `uv run pytest tests/path_to_test.py::test_function`
- Run with coverage: `uv run pytest --cov=openapi_mcp`
- Debug test: `uv run pytest -xvs tests/path_to_test.py::test_function`

## Linting & Formatting
- Format code: `uv run black src tests`
- Lint code: `uv run ruff src tests`
- Type check: `uv run mypy src`
- Run all checks: `uv run black src tests && uv run ruff src tests && uv run mypy src`

## Code Style Guidelines
- Line length: 88 characters (Black default)
- Python: 3.10+ with strict typing (disallow_untyped_defs = true)
- Docstrings: Use triple-quoted strings with """description"""
- Imports: Use absolute imports, sorted by ruff (select = ["E", "F", "I"])
- Naming: snake_case for functions/variables, CamelCase for classes
- Type hints: Required for all functions and class attributes
- Error handling: Use specific exceptions with meaningful messages
- Dependencies: mcp, pyyaml, click, requests (with pytest, black, ruff, mypy for dev)

## Project Tracking
- GitHub Project: https://github.com/users/brukhabtu/projects/2
- Check current priorities: `gh project item-list 2 --owner brukhabtu --format json`
- View Todo issues: `gh api graphql -f query='query{user(login:"brukhabtu"){projectV2(number:2){items(first:100){nodes{content{...on Issue{title number labels{nodes{name}} milestone{title}}}}}}}}' | grep "Todo"`
- View In Progress: `gh issue list --repo brukhabtu/openapi-mcp --state open --label "status:in-progress"`
- View milestones: `gh api repos/brukhabtu/openapi-mcp/milestones`
- Development plan: See DEVELOPMENT_PLAN.md