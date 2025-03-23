"""
Client generator module for OpenAPI-MCP.

This module provides functionality to generate Python clients from
OpenAPI specifications using openapi-python-client.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json

from openapi_python_client import GeneratorError, generate
from openapi_python_client.config import ConfigFile, Config, MetaType

from openapi_mcp.spec_processor import SpecProcessor


class ClientGenerator:
    """
    Generate Python clients from OpenAPI specifications.

    This class provides methods to generate Python client libraries from
    OpenAPI specifications using openapi-python-client.
    """

    def __init__(self, spec_processor: Optional[SpecProcessor] = None) -> None:
        """
        Initialize the client generator.

        Args:
            spec_processor: Optional SpecProcessor instance with a loaded spec
        """
        self.spec_processor = spec_processor or SpecProcessor()

    def load_spec(self, spec_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load an OpenAPI specification.

        Args:
            spec_path: Path or URL to the OpenAPI specification

        Returns:
            Dict containing the parsed OpenAPI specification

        Raises:
            ValueError: If the spec path is invalid or the spec is invalid
        """
        if isinstance(spec_path, str) and spec_path.startswith(("http://", "https://")):
            return self.spec_processor.load_from_url(spec_path)
        else:
            return self.spec_processor.load_from_file(spec_path)

    def generate_client(
        self,
        output_dir: Union[str, Path],
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Generate a Python client from the loaded OpenAPI specification.

        Args:
            output_dir: Directory where the generated client will be saved
            config: Optional configuration for the generator

        Returns:
            Path to the generated client

        Raises:
            ValueError: If no specification is loaded
            RuntimeError: If the client generation fails
        """
        if not hasattr(self.spec_processor, "spec") or not self.spec_processor.spec:
            raise ValueError("No specification loaded. Call load_spec() first.")

        # Create temporary directory for spec file
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_spec_path = Path(temp_dir) / "openapi.json"

            # Write the spec to a temporary file
            with open(temp_spec_path, "w", encoding="utf-8") as f:
                json.dump(self.spec_processor.spec, f)

            # Prepare output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Create a default config
            config_file = ConfigFile()

            # Convert custom config settings if provided
            if config:
                # Map camelCase to snake_case for compatibility
                if "packageName" in config:
                    config["package_name_override"] = config.pop("packageName")
                if "projectName" in config:
                    config["project_name_override"] = config.pop("projectName")

                # Apply configuration to ConfigFile
                for key, value in config.items():
                    if hasattr(config_file, key):
                        setattr(config_file, key, value)

            # Generate the final Config from ConfigFile
            generator_config = Config.from_sources(
                config_file=config_file,
                meta_type=MetaType.NONE,  # No meta builder like Poetry or PDM
                document_source=temp_spec_path,
                file_encoding="utf-8",
                overwrite=True,
                output_path=output_path,
            )

            try:
                # Generate client
                result = generate(config=generator_config)

                if result:  # If there are any errors
                    error_details = ", ".join(str(error) for error in result)
                    raise RuntimeError(f"Client generation failed: {error_details}")

                # Return the path to the generated client
                return output_path

            except Exception as e:
                raise RuntimeError(f"Failed to generate client: {str(e)}")

    def validate_generated_client(self, client_dir: Union[str, Path]) -> bool:
        """
        Validate the generated client.

        Args:
            client_dir: Directory containing the generated client

        Returns:
            True if the client is valid

        Raises:
            ValueError: If the client directory does not exist or is invalid
        """
        client_dir = Path(client_dir)

        if not client_dir.exists() or not client_dir.is_dir():
            raise ValueError(f"Client directory does not exist: {client_dir}")

        # Check for package structure
        package_name = None

        # Try to find a Python package in the client directory
        for item in client_dir.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                package_name = item.name
                break

        if not package_name:
            raise ValueError("Invalid client: No Python package found")

        # Check for key files
        required_files = [
            f"{package_name}/__init__.py",
            f"{package_name}/client.py",
            "pyproject.toml",
        ]

        for rel_path in required_files:
            if not (client_dir / rel_path).exists():
                raise ValueError(f"Invalid client: missing {rel_path}")

        return True

    def package_client(
        self,
        client_dir: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        Package the generated client into a distribution format.

        Args:
            client_dir: Directory containing the generated client
            output_file: Optional path for the packaged client

        Returns:
            Path to the packaged client

        Raises:
            ValueError: If the client directory does not exist
            RuntimeError: If the packaging fails
        """
        client_dir = Path(client_dir)

        if not client_dir.exists() or not client_dir.is_dir():
            raise ValueError(f"Client directory does not exist: {client_dir}")

        # Validate the client first
        self.validate_generated_client(client_dir)

        # Change to the client directory and build the package
        current_dir = os.getcwd()
        try:
            os.chdir(client_dir)

            # Execute pip to build distribution
            import subprocess

            cmd = ["python", "-m", "build", "--wheel"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Client packaging failed: {result.stderr}")

            # Find the wheel file
            dist_dir = client_dir / "dist"
            wheels = list(dist_dir.glob("*.whl"))

            if not wheels:
                raise RuntimeError("No wheel file found after packaging")

            # Get the most recent wheel
            wheel_path = max(wheels, key=lambda p: p.stat().st_mtime)

            # Copy to the output location if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(wheel_path, output_path)
                return output_path

            return wheel_path

        except Exception as e:
            raise RuntimeError(f"Failed to package client: {str(e)}")
        finally:
            os.chdir(current_dir)
