"""
OpenAPI specification processor module.

This module provides functionality to load, validate, and process
OpenAPI specifications.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json
import os
import yaml
import requests
from urllib.parse import urlparse


class SpecProcessor:
    """
    Process OpenAPI specifications from file or URL.

    This class provides methods to load, validate, and extract information from
    OpenAPI specifications.
    """

    def __init__(self) -> None:
        """Initialize the spec processor."""
        self.spec: Dict[str, Any] = {}

    def load_from_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load an OpenAPI specification from a file.

        Args:
            file_path: Path to the OpenAPI specification file (JSON or YAML)

        Returns:
            Dict containing the parsed OpenAPI specification

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file format is not supported or content is invalid
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Specification file not found: {file_path}")

        # Read and parse based on file extension
        suffix = file_path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    self.spec = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise ValueError(f"Invalid YAML format: {e}")
        elif suffix == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    self.spec = json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON format: {e}")
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        # Validate the loaded spec
        self.validate_spec()

        return self.spec

    def load_from_url(self, url: str) -> Dict[str, Any]:
        """
        Load an OpenAPI specification from a URL.

        Args:
            url: URL pointing to an OpenAPI specification (JSON or YAML)

        Returns:
            Dict containing the parsed OpenAPI specification

        Raises:
            ValueError: If the URL is invalid or content cannot be parsed
            requests.RequestException: If the request fails
        """
        # Basic URL validation
        parsed_url = urlparse(url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise ValueError(f"Invalid URL: {url}")

        # Fetch the spec from URL
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")

        # Parse based on content type or try to infer format
        if "application/json" in content_type:
            try:
                self.spec = response.json()
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON response: {e}")
        elif any(
            fmt in content_type
            for fmt in ["application/yaml", "application/x-yaml", "text/yaml"]
        ):
            try:
                self.spec = yaml.safe_load(response.text)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML response: {e}")
        else:
            # Try to infer format from content
            try:
                self.spec = response.json()
            except json.JSONDecodeError:
                try:
                    self.spec = yaml.safe_load(response.text)
                except yaml.YAMLError:
                    raise ValueError("Could not parse response as JSON or YAML")

        # Validate the loaded spec
        self.validate_spec()

        return self.spec

    def validate_spec(self) -> bool:
        """
        Validate the loaded OpenAPI specification.

        Returns:
            True if the specification is valid

        Raises:
            ValueError: If the specification is invalid
        """
        if not self.spec:
            raise ValueError("No specification loaded")

        # Basic structure validation
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            if field not in self.spec:
                raise ValueError(
                    f"Invalid OpenAPI specification: missing required field '{field}'"
                )

        # Validate OpenAPI version
        openapi_version = self.spec.get("openapi", "")
        if not openapi_version.startswith(("3.0", "3.1")):
            raise ValueError(
                f"Unsupported OpenAPI version: {openapi_version}. "
                f"Expected 3.0.x or 3.1.x"
            )

        # Validate info section
        info = self.spec.get("info", {})
        if not isinstance(info, dict) or "title" not in info or "version" not in info:
            raise ValueError(
                "Invalid 'info' section: must contain 'title' and 'version'"
            )

        # Validate paths section
        paths = self.spec.get("paths", {})
        if not isinstance(paths, dict):
            raise ValueError("Invalid 'paths' section: must be an object")

        return True

    def extract_endpoints(self) -> List[Dict[str, Any]]:
        """
        Extract API endpoints from the specification.

        Returns:
            List of dictionaries containing endpoint information

        Raises:
            ValueError: If no specification is loaded
        """
        if not self.spec:
            raise ValueError("No specification loaded")

        endpoints = []
        paths = self.spec.get("paths", {})

        for path, path_item in paths.items():
            for method, operation in path_item.items():
                # Skip non-operation properties like parameters
                if method in ["parameters", "servers", "summary", "description"]:
                    continue

                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "operation_id": operation.get("operationId"),
                    "summary": operation.get("summary"),
                    "description": operation.get("description"),
                    "parameters": operation.get("parameters", []),
                    "request_body": operation.get("requestBody"),
                    "responses": operation.get("responses", {}),
                }
                endpoints.append(endpoint)

        return endpoints

    def get_schemas(self) -> Dict[str, Any]:
        """
        Extract schema definitions from the specification.

        Returns:
            Dictionary of schema definitions

        Raises:
            ValueError: If no specification is loaded
        """
        if not self.spec:
            raise ValueError("No specification loaded")

        components = self.spec.get("components", {})
        schemas = components.get("schemas", {})

        # Explicitly cast to correct return type to satisfy mypy
        return dict(schemas)
