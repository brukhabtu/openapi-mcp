"""
Client generator module for OpenAPI-MCP.

This module provides functionality to generate Python clients from
OpenAPI specifications using openapi-generator-cli.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from openapi_mcp.spec_processor import SpecProcessor


class ClientGenerator:
    """
    Generate Python clients from OpenAPI specifications.
    
    This class provides methods to generate Python client libraries from
    OpenAPI specifications using openapi-generator-cli.
    """
    
    def __init__(self, spec_processor: Optional[SpecProcessor] = None) -> None:
        """
        Initialize the client generator.
        
        Args:
            spec_processor: Optional SpecProcessor instance with a loaded spec
        """
        self.spec_processor = spec_processor or SpecProcessor()
        self._check_generator_cli()
    
    def _check_generator_cli(self) -> None:
        """
        Check if openapi-generator-cli is available.
        
        Raises:
            RuntimeError: If openapi-generator-cli is not available
        """
        try:
            result = subprocess.run(
                ["openapi-generator-cli", "version"],
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                raise RuntimeError(
                    "openapi-generator-cli is not available. "
                    "Please install it first: npm install @openapitools/openapi-generator-cli -g"
                )
        except FileNotFoundError:
            raise RuntimeError(
                "openapi-generator-cli is not available. "
                "Please install it first: npm install @openapitools/openapi-generator-cli -g"
            )
    
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
                import json
                json.dump(self.spec_processor.spec, f)
            
            # Prepare output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Basic configuration
            base_config = {
                "generateSourceCodeOnly": "true",
                "packageName": "openapi_client",
                "library": "urllib3",
            }
            
            # Merge with user config
            if config:
                base_config.update(config)
            
            # Prepare config options
            config_options = [
                f"--additional-properties={key}={value}"
                for key, value in base_config.items()
            ]
            
            # Execute openapi-generator-cli
            cmd = [
                "openapi-generator-cli", "generate",
                "-i", str(temp_spec_path),
                "-g", "python",
                "-o", str(output_path),
                *config_options,
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                
                if result.returncode != 0:
                    raise RuntimeError(
                        f"Client generation failed: {result.stderr}"
                    )
            except Exception as e:
                raise RuntimeError(f"Failed to generate client: {str(e)}")
            
            return output_path
    
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
        
        # Check for key files
        required_files = [
            "openapi_client/__init__.py",
            "openapi_client/api_client.py",
            "setup.py",
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
            
            # Execute setup.py to build distribution
            cmd = ["python", "setup.py", "sdist", "bdist_wheel"]
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