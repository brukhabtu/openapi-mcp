"""
Command-line interface for OpenAPI-MCP.
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Any

import click
import requests
import json

from openapi_mcp.spec_processor import SpecProcessor
from openapi_mcp.client_generator import ClientGenerator


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
    type=str,
)
@click.option(
    "--output", "-o",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help="Output directory for generated client",
)
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Path to generator configuration JSON file",
)
@click.option(
    "--package", "-p",
    is_flag=True,
    help="Package the generated client as a wheel",
)
def generate_client(spec_path: str, output: Path, config: Optional[str] = None, package: bool = False) -> None:
    """
    Generate a Python client from an OpenAPI specification.
    
    SPEC_PATH can be a local file path or a URL pointing to an OpenAPI specification.
    """
    try:
        # Load configuration if provided
        generator_config: Dict[str, Any] = {}
        if config:
            with open(config, "r", encoding="utf-8") as f:
                generator_config = json.load(f)
        
        click.echo(f"Generating Python client from {spec_path} to {output}")
        
        # Initialize generator
        generator = ClientGenerator()
        
        # Load specification
        try:
            generator.load_spec(spec_path)
            click.secho("✓ OpenAPI specification loaded and validated", fg="green")
        except (ValueError, FileNotFoundError, requests.RequestException) as e:
            click.secho(f"Error: Failed to load specification: {str(e)}", fg="red", err=True)
            sys.exit(1)
        
        # Generate client
        try:
            client_dir = generator.generate_client(output, generator_config)
            click.secho(f"✓ Client generated successfully at {client_dir}", fg="green")
        except RuntimeError as e:
            click.secho(f"Error: Failed to generate client: {str(e)}", fg="red", err=True)
            sys.exit(1)
        
        # Package client if requested
        if package:
            try:
                click.echo("Packaging client as wheel...")
                wheel_path = generator.package_client(client_dir)
                click.secho(f"✓ Client packaged successfully: {wheel_path}", fg="green")
            except (ValueError, RuntimeError) as e:
                click.secho(f"Error: Failed to package client: {str(e)}", fg="red", err=True)
                sys.exit(1)
        
    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red", err=True)
        sys.exit(1)


@main.command()
@click.argument(
    "spec_path",
    type=str,
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed information about the specification",
)
def validate(spec_path: str, verbose: bool) -> None:
    """
    Validate an OpenAPI specification file or URL.
    
    SPEC_PATH can be a local file path or a URL pointing to an OpenAPI specification.
    """
    processor = SpecProcessor()
    
    try:
        # Determine if path is URL or file
        if spec_path.startswith(("http://", "https://")):
            click.echo(f"Validating OpenAPI specification from URL: {spec_path}")
            spec = processor.load_from_url(spec_path)
        else:
            file_path = Path(spec_path)
            if not file_path.exists():
                click.echo(f"Error: File not found: {spec_path}", err=True)
                sys.exit(1)
            
            click.echo(f"Validating OpenAPI specification file: {spec_path}")
            spec = processor.load_from_file(file_path)
        
        # Basic validation is already done in the processor
        
        # Display validation success
        click.secho("✓ Valid OpenAPI specification", fg="green")
        
        # Show additional information if verbose
        if verbose:
            info = spec.get("info", {})
            click.echo(f"\nTitle: {info.get('title', 'Not specified')}")
            click.echo(f"Version: {info.get('version', 'Not specified')}")
            click.echo(f"OpenAPI Version: {spec.get('openapi', 'Not specified')}")
            
            # Count endpoints
            endpoints = processor.extract_endpoints()
            click.echo(f"Endpoints: {len(endpoints)}")
            
            # Count schemas
            schemas = processor.get_schemas()
            click.echo(f"Schemas: {len(schemas)}")
            
            # Show endpoint summary if there are any
            if endpoints:
                click.echo("\nEndpoints:")
                for endpoint in endpoints:
                    method = endpoint['method']
                    path = endpoint['path']
                    summary = endpoint['summary'] or 'No summary'
                    click.echo(f"  {method} {path} - {summary}")
        
    except (ValueError, FileNotFoundError, requests.RequestException) as e:
        click.secho(f"Error: {str(e)}", fg="red", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()