import os
import unittest
from pathlib import Path
import json
import tempfile
from unittest.mock import patch, MagicMock

from openapi_mcp.spec_processor import SpecProcessor


class TestSpecProcessor(unittest.TestCase):
    """Test the OpenAPI specification processor."""

    def setUp(self):
        """Set up test fixtures."""
        self.examples_dir = Path(__file__).parents[2] / "examples"
        self.petstore_spec = self.examples_dir / "petstore" / "openapi.yaml"

    def test_load_spec_from_file(self):
        """Test loading an OpenAPI spec from a file."""
        self.assertTrue(os.path.exists(self.petstore_spec))
        processor = SpecProcessor()
        spec = processor.load_from_file(self.petstore_spec)
        self.assertIsNotNone(spec)
        self.assertEqual(spec["info"]["title"], "Petstore API")
        self.assertEqual(spec["info"]["version"], "1.0.0")
        self.assertIn("paths", spec)
        self.assertIn("/pets", spec["paths"])

    def test_load_spec_from_file_json(self):
        """Test loading an OpenAPI spec from a JSON file."""
        # Create a temporary JSON file with the OpenAPI spec
        temp_path = Path(tempfile.mktemp(suffix=".json"))
        try:
            # Convert YAML to JSON and write to temp file
            processor = SpecProcessor()
            yaml_spec = processor.load_from_file(self.petstore_spec)

            with open(temp_path, "w", encoding="utf-8") as temp_file:
                json.dump(yaml_spec, temp_file)

            # Load from JSON file
            processor = SpecProcessor()
            json_spec = processor.load_from_file(temp_path)
            self.assertEqual(json_spec["info"]["title"], "Petstore API")
            self.assertEqual(json_spec["info"]["version"], "1.0.0")
        finally:
            # Cleanup the temp file
            if temp_path.exists():
                os.unlink(temp_path)

    def test_load_spec_file_not_found(self):
        """Test error handling when file is not found."""
        processor = SpecProcessor()
        with self.assertRaises(FileNotFoundError):
            processor.load_from_file("/non/existent/file.yaml")

    def test_load_spec_invalid_format(self):
        """Test error handling for invalid file format."""
        processor = SpecProcessor()
        with self.assertRaises(ValueError):
            processor.load_from_file(__file__)  # Try to load this Python file

    @patch("requests.get")
    def test_load_spec_from_url(self, mock_get):
        """Test loading an OpenAPI spec from a URL."""
        # Create a mock response with the OpenAPI spec
        processor = SpecProcessor()
        yaml_spec = processor.load_from_file(self.petstore_spec)

        mock_response = MagicMock()
        mock_response.json.return_value = yaml_spec
        mock_response.text = "dummy yaml content"
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status = MagicMock()

        mock_get.return_value = mock_response

        # Test loading from URL
        processor = SpecProcessor()
        spec = processor.load_from_url("https://example.com/api.json")

        self.assertEqual(spec["info"]["title"], "Petstore API")
        self.assertEqual(spec["info"]["version"], "1.0.0")
        mock_get.assert_called_once_with("https://example.com/api.json", timeout=30)

    def test_validate_spec(self):
        """Test validating an OpenAPI specification."""
        processor = SpecProcessor()
        processor.load_from_file(self.petstore_spec)

        # Valid spec should return True
        self.assertTrue(processor.validate_spec())

        # Test with invalid spec
        processor = SpecProcessor()
        with self.assertRaises(ValueError):
            processor.validate_spec()  # No spec loaded

    def test_extract_endpoints(self):
        """Test extracting API endpoints from the specification."""
        processor = SpecProcessor()
        processor.load_from_file(self.petstore_spec)

        endpoints = processor.extract_endpoints()
        self.assertIsInstance(endpoints, list)
        self.assertGreater(len(endpoints), 0)

        # Verify endpoint structure
        # Find an endpoint by path and method
        pets_endpoint = [
            ep for ep in endpoints if ep["path"] == "/pets" and ep["method"] == "GET"
        ][0]
        self.assertEqual(pets_endpoint["operation_id"], "listPets")
        self.assertEqual(pets_endpoint["summary"], "List all pets")
        self.assertIn("parameters", pets_endpoint)

    def test_get_schemas(self):
        """Test extracting schema definitions from the specification."""
        processor = SpecProcessor()
        processor.load_from_file(self.petstore_spec)

        schemas = processor.get_schemas()
        self.assertIsInstance(schemas, dict)
        self.assertIn("Pet", schemas)
        self.assertIn("NewPet", schemas)

        # Verify schema structure
        pet_schema = schemas["Pet"]
        self.assertIn("properties", pet_schema)
        self.assertIn("id", pet_schema["properties"])
        self.assertIn("name", pet_schema["properties"])


if __name__ == "__main__":
    unittest.main()
