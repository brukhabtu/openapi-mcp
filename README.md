# OpenAPI-MCP

A tool for converting OpenAPI specifications into Model Context Protocol (MCP) servers.

## Overview

OpenAPI-MCP bridges the gap between REST APIs and large language models by:

1. Taking an OpenAPI specification as input
2. Generating a Python client for the API
3. Creating an MCP wrapper that exposes the API to language models

This allows any API defined with an OpenAPI spec to be used as an MCP server, making it accessible to Claude and other LLMs through the Model Context Protocol.

## Project Status

This project is under active development following our [development plan](DEVELOPMENT_PLAN.md).

## Features (Planned)

- Convert GET endpoints to MCP Resources
- Convert POST/PUT/DELETE endpoints to MCP Tools
- Support for path parameters, query parameters, and request bodies
- Authentication handling
- Type conversion between OpenAPI schemas and Python types
- Command-line interface for easy usage
- Customization options for special cases

## Installation

```bash
# Not yet available - project in development
pip install openapi-mcp
```

## Usage

```bash
# Basic usage (planned)
openapi-mcp generate --spec path/to/openapi.yaml --output my_api_mcp

# Run the generated MCP server
cd my_api_mcp
python -m my_api_mcp
```

## Development

See the [Development Plan](DEVELOPMENT_PLAN.md) for details on the project roadmap.

```bash
# Development setup
git clone https://github.com/brukhabtu/openapi-mcp.git
cd openapi-mcp
uv venv
source .venv/bin/activate  # On Unix-like systems
# or .venv\Scripts\activate  # On Windows
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run linting and type checking
uv run black src tests
uv run ruff src tests
uv run mypy src
```

## License

MIT