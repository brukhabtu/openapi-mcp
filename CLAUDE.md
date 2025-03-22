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
- Run integration tests: `uv run pytest tests/integration/`

## Formatting & Type Checking
- Format code: `uv run black src tests`
- Type check: `uv run mypy src`
- Run all checks: `uv run black src tests && uv run mypy src`

## CI/CD
- CI runs on pull requests and pushes to main
- Automated checks: Black, MyPy, Pytest
- Release workflow triggers on tags with format `v*.*.*`
- See .github/workflows/ for configuration details
- Contributing guide: .github/CONTRIBUTING.md

## Code Style Guidelines
- Line length: 88 characters (Black default)
- Python: 3.10+ with strict typing (disallow_untyped_defs = true)
- Docstrings: Use triple-quoted strings with """description"""
- Imports: Use absolute imports
- Naming: snake_case for functions/variables, CamelCase for classes
- Type hints: Required for all functions and class attributes
- Error handling: Use specific exceptions with meaningful messages
- Unit tests: Use unittest.TestCase with descriptive method names
- Test naming: Use test_*.py for test files and test_* for test methods
- Dependencies: mcp, pyyaml, click, requests (with pytest, black, mypy for dev)
- Module structure: Organize code in logical modules following the project structure

## Project Phases & Milestones
- Phase 1: Foundation and Core Functionality (spec processing, client generation)
- Phase 2: MCP Wrapper Generation (resource mapping, tool mapping)
- Phase 3: Enhancement and Polish (schema improvements, testing, CLI)
- Phase 4: Advanced Features (customization, authentication, optimization)
- Development plan: See GitHub project for detailed timeline

## Project Tracking
- GitHub Project: https://github.com/users/brukhabtu/projects/2
- View Todo issues: `gh issue list --repo brukhabtu/openapi-mcp --state open --label "status:todo"`
- View In Progress: `gh issue list --repo brukhabtu/openapi-mcp --state open --label "status:in-progress"`
- Monitor CI status: `./scripts/ci_status.sh`
- Watch CI pipeline: `./scripts/watch_ci.sh`