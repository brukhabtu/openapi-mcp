"""
Command-line interface for OpenAPI-MCP.
"""

import click
from pathlib import Path


@click.group()
def main() -> None:
    """Convert OpenAPI specifications into Model Context Protocol servers."""
    pass


@main.command()
@click.option(
    "--spec",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to OpenAPI specification file (JSON or YAML)",
)
@click.option(
    "--output",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help="Output directory for generated code",
)
def generate(spec: Path, output: Path) -> None:
    """Generate an MCP server from an OpenAPI specification."""
    click.echo(f"Generating MCP server from {spec} to {output}")
    # Implementation will be added in future phases


@main.command()
@click.argument(
    "spec_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
def validate(spec_path: Path) -> None:
    """Validate an OpenAPI specification file."""
    click.echo(f"Validating OpenAPI specification at {spec_path}")
    # Implementation will be added in future phases
    click.echo("Valid OpenAPI specification")


if __name__ == "__main__":
    main()
