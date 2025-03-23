# OpenAPI-MCP

A tool for converting OpenAPI specifications into Model Context Protocol (MCP) servers.

## Overview

OpenAPI-MCP bridges the gap between REST APIs and large language models by:

1. Taking an OpenAPI specification as input
2. Generating a Python client for the API using [openapi-python-client](https://github.com/openapi-generators/openapi-python-client)
3. Creating an MCP wrapper that exposes the API to language models

This allows any API defined with an OpenAPI spec to be used as an MCP server, making it accessible to Claude and other LLMs through the Model Context Protocol.

The generated Python client features modern Python practices including type annotations, dataclasses, and async support.

## Project Status

This project is under active development. See our GitHub project board for status.

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

No external dependencies like npm or Node.js are required, as this tool uses pure Python libraries.

## Usage

```bash
# Basic usage (planned)
openapi-mcp generate --spec path/to/openapi.yaml --output my_api_mcp

# Run the generated MCP server
cd my_api_mcp
python -m my_api_mcp
```

## Development

See our GitHub project board for details on the project roadmap.

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

# Run formatting and type checking
uv run black src tests
uv run mypy src
```

## License

MIT