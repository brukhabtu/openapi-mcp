# Contributing to OpenAPI-MCP

Thank you for considering contributing to OpenAPI-MCP! This document outlines the process for contributing to the project.

## Development Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run formatting, type checking, and tests locally:
   ```bash
   uv run black src tests
   uv run mypy src
   uv run pytest
   ```
5. Commit your changes with a descriptive message
6. Push to your fork: `git push origin feature/my-feature`
7. Open a Pull Request

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment:

- **CI Workflow**: Runs on every push to main and on every pull request
  - Uses [astral-sh/setup-uv](https://github.com/astral-sh/setup-uv) to install and cache uv
  - Formatting checks with Black and type checking with MyPy
  - Tests with Pytest on multiple Python versions (3.10, 3.11)

- **Release Workflow**: Runs when a tag with format `v*.*.*` is pushed
  - Builds the package
  - Creates a GitHub Release with the built distributions
  - (When configured) Publishes to PyPI

## Versioning

We follow [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for functionality added in a backward compatible manner
- PATCH version for backward compatible bug fixes

## Code Style

Please adhere to the code style guidelines defined in the project:

- Use Black for formatting
- Include proper type annotations (checked by MyPy)
- Write docstrings for all public modules, functions, classes, and methods

## Pull Request Process

1. Ensure all tests pass locally before submitting
2. Update documentation if needed
3. Submit PR against the main branch
4. Wait for reviews and address any feedback
5. PRs need approval before they can be merged

Thank you for your contributions!