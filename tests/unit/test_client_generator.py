"""
Unit tests for the client_generator module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

from openapi_mcp.client_generator import ClientGenerator
from openapi_mcp.spec_processor import SpecProcessor


@pytest.fixture
def sample_spec() -> dict:
    """Return a sample OpenAPI specification for testing."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
        },
        "paths": {
            "/test": {
                "get": {
                    "operationId": "testOperation",
                    "responses": {
                        "200": {
                            "description": "OK",
                        }
                    },
                }
            }
        },
    }


@pytest.fixture
def spec_file(sample_spec, tmp_path):
    """Create a temporary spec file for testing."""
    spec_file = tmp_path / "openapi.yaml"
    with open(spec_file, "w", encoding="utf-8") as f:
        yaml.dump(sample_spec, f)
    return spec_file


class TestClientGenerator:
    """Tests for the ClientGenerator class."""

    def test_load_spec_from_file(self, spec_file):
        """Test loading a spec from a file."""
        generator = ClientGenerator()
        with mock.patch.object(SpecProcessor, "load_from_file") as mock_load:
            mock_load.return_value = {"openapi": "3.0.0"}
            result = generator.load_spec(spec_file)
            mock_load.assert_called_once_with(spec_file)
            assert result == {"openapi": "3.0.0"}

    def test_load_spec_from_url(self):
        """Test loading a spec from a URL."""
        url = "https://example.com/openapi.yaml"
        generator = ClientGenerator()
        with mock.patch.object(SpecProcessor, "load_from_url") as mock_load:
            mock_load.return_value = {"openapi": "3.0.0"}
            result = generator.load_spec(url)
            mock_load.assert_called_once_with(url)
            assert result == {"openapi": "3.0.0"}

    def test_generate_client_without_loaded_spec(self, tmp_path):
        """Test generating a client without a loaded spec."""
        generator = ClientGenerator()
        with pytest.raises(ValueError) as excinfo:
            generator.generate_client(tmp_path)
        assert "No specification loaded" in str(excinfo.value)

    def test_generate_client(self, sample_spec, tmp_path):
        """Test generating a client."""
        # Create instance of ClientGenerator with mocked dependencies
        with mock.patch("openapi_mcp.client_generator.generate") as mock_generate:
            mock_generate.return_value = []  # No errors

            generator = ClientGenerator()
            generator.spec_processor.spec = sample_spec

            # Make TemporaryDirectory context manager return a predictable path
            temp_dir = "/tmp/mock-temp-dir"
            mock_temp_dir = mock.MagicMock()
            mock_temp_dir.__enter__.return_value = temp_dir

            with (
                mock.patch("tempfile.TemporaryDirectory", return_value=mock_temp_dir),
                mock.patch("builtins.open", mock.mock_open()),
            ):

                output_path = generator.generate_client(tmp_path)
                assert output_path == Path(tmp_path)

                # Verify generate was called
                assert mock_generate.called

    def test_generate_client_with_config(self, sample_spec, tmp_path):
        """Test generating a client with custom configuration."""
        user_config = {
            "packageName": "custom_package",
            "project_name_override": "CustomClient",
        }

        # Create a mock for generate that captures the config passed
        generate_mock = mock.MagicMock(return_value=[])

        with mock.patch("openapi_mcp.client_generator.generate", generate_mock):
            generator = ClientGenerator()
            generator.spec_processor.spec = sample_spec

            # Make TemporaryDirectory context manager return a predictable path
            temp_dir = "/tmp/mock-temp-dir"
            mock_temp_dir = mock.MagicMock()
            mock_temp_dir.__enter__.return_value = temp_dir

            with (
                mock.patch("tempfile.TemporaryDirectory", return_value=mock_temp_dir),
                mock.patch("builtins.open", mock.mock_open()),
            ):

                generator.generate_client(tmp_path, user_config)

                # Check the generator was called
                generate_mock.assert_called_once()

                # Get the config that was passed to generate
                args, kwargs = generate_mock.call_args
                assert "config" in kwargs

    def test_generate_client_error(self, sample_spec, tmp_path):
        """Test handling of errors during generation."""
        from openapi_python_client import GeneratorError

        # Mock a generation error - return list of errors
        error = GeneratorError(header="Generation failed", detail="Error details")

        # Create a mock for generate that returns an error
        with mock.patch("openapi_mcp.client_generator.generate") as generate_mock:
            generate_mock.return_value = [error]

            generator = ClientGenerator()
            generator.spec_processor.spec = sample_spec

            # Make TemporaryDirectory context manager return a predictable path
            temp_dir = "/tmp/mock-temp-dir"
            mock_temp_dir = mock.MagicMock()
            mock_temp_dir.__enter__.return_value = temp_dir

            with (
                mock.patch("tempfile.TemporaryDirectory", return_value=mock_temp_dir),
                mock.patch("builtins.open", mock.mock_open()),
            ):

                with pytest.raises(RuntimeError) as excinfo:
                    generator.generate_client(tmp_path)
                assert "Client generation failed" in str(excinfo.value)

    def test_validate_generated_client(self, tmp_path):
        """Test validating a generated client."""
        generator = ClientGenerator()

        # Create a fake client directory structure
        client_dir = tmp_path / "client"
        package_dir = client_dir / "test_client"
        os.makedirs(package_dir)
        (package_dir / "__init__.py").touch()
        (package_dir / "client.py").touch()
        (client_dir / "pyproject.toml").touch()

        # Should validate successfully
        assert generator.validate_generated_client(client_dir) is True

    def test_validate_generated_client_missing_files(self, tmp_path):
        """Test validating a client with missing files."""
        generator = ClientGenerator()

        # Create an incomplete client directory structure
        client_dir = tmp_path / "client"
        package_dir = client_dir / "test_client"
        os.makedirs(package_dir)
        (package_dir / "__init__.py").touch()
        # Missing client.py and pyproject.toml

        with pytest.raises(ValueError) as excinfo:
            generator.validate_generated_client(client_dir)
        assert "Invalid client: missing" in str(excinfo.value)

    def test_package_client(self, tmp_path):
        """Test packaging a generated client."""
        generator = ClientGenerator()

        # Create a fake client directory structure
        client_dir = tmp_path / "client"
        package_dir = client_dir / "test_client"
        os.makedirs(package_dir)
        (package_dir / "__init__.py").touch()
        (package_dir / "client.py").touch()
        (client_dir / "pyproject.toml").touch()

        # Create a fake dist directory with a wheel
        os.makedirs(client_dir / "dist")
        wheel_path = client_dir / "dist" / "test_client-1.0.0-py3-none-any.whl"
        wheel_path.touch()

        with mock.patch("subprocess.run") as mock_run, mock.patch("os.chdir"):
            mock_result = mock.MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = generator.package_client(client_dir)
            assert result == wheel_path

    def test_package_client_with_output_path(self, tmp_path):
        """Test packaging a client with a custom output path."""
        generator = ClientGenerator()

        # Create a fake client directory structure
        client_dir = tmp_path / "client"
        package_dir = client_dir / "test_client"
        os.makedirs(package_dir)
        (package_dir / "__init__.py").touch()
        (package_dir / "client.py").touch()
        (client_dir / "pyproject.toml").touch()

        # Create a fake dist directory with a wheel
        os.makedirs(client_dir / "dist")
        wheel_path = client_dir / "dist" / "test_client-1.0.0-py3-none-any.whl"
        wheel_path.touch()

        output_path = tmp_path / "output" / "custom.whl"

        with (
            mock.patch("subprocess.run") as mock_run,
            mock.patch("os.chdir"),
            mock.patch("shutil.copy") as mock_copy,
        ):
            mock_result = mock.MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = generator.package_client(client_dir, output_path)
            assert result == output_path
            mock_copy.assert_called_once_with(wheel_path, output_path)

    def test_package_client_no_wheel(self, tmp_path):
        """Test packaging when no wheel is generated."""
        generator = ClientGenerator()

        # Create a fake client directory structure
        client_dir = tmp_path / "client"
        package_dir = client_dir / "test_client"
        os.makedirs(package_dir)
        (package_dir / "__init__.py").touch()
        (package_dir / "client.py").touch()
        (client_dir / "pyproject.toml").touch()

        # Create an empty dist directory (no wheel)
        os.makedirs(client_dir / "dist")

        with mock.patch("subprocess.run") as mock_run, mock.patch("os.chdir"):
            mock_result = mock.MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            with pytest.raises(RuntimeError) as excinfo:
                generator.package_client(client_dir)
            assert "No wheel file found" in str(excinfo.value)
