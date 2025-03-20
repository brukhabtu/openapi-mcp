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


@pytest.fixture
def mock_generator():
    """Mock the openapi-generator-cli commands."""
    with mock.patch("subprocess.run") as mock_run:
        # Mock the version check
        version_result = mock.MagicMock()
        version_result.returncode = 0
        version_result.stdout = "5.0.0"
        
        # Mock the generate command
        generate_result = mock.MagicMock()
        generate_result.returncode = 0
        
        # Mock the package command
        package_result = mock.MagicMock()
        package_result.returncode = 0
        
        # Set up the side effects for different commands
        def side_effect(cmd, **kwargs):
            if "version" in cmd:
                return version_result
            elif "generate" in cmd:
                return generate_result
            elif "setup.py" in cmd:
                return package_result
            return mock.MagicMock()
        
        mock_run.side_effect = side_effect
        yield mock_run


class TestClientGenerator:
    """Tests for the ClientGenerator class."""
    
    def test_init_checks_generator_cli(self, mock_generator):
        """Test that initialization checks for the openapi-generator-cli."""
        generator = ClientGenerator()
        mock_generator.assert_called_once()
        
    def test_init_with_missing_cli(self):
        """Test initialization when openapi-generator-cli is not available."""
        with mock.patch("subprocess.run", side_effect=FileNotFoundError()):
            with pytest.raises(RuntimeError) as excinfo:
                ClientGenerator()
            assert "openapi-generator-cli is not available" in str(excinfo.value)
    
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
    
    def test_generate_client(self, sample_spec, tmp_path, mock_generator):
        """Test generating a client."""
        generator = ClientGenerator()
        generator.spec_processor.spec = sample_spec
        
        # Mock the file operations
        with mock.patch("builtins.open", mock.mock_open()) as mock_file:
            output_path = generator.generate_client(tmp_path)
            assert output_path == Path(tmp_path)
            
            # Check that the spec was written to a temporary file
            mock_file.assert_called()
            
            # Check that the generator was called with the right arguments
            mock_generator.assert_called()
            
            # Check the last call to mock_generator
            args, kwargs = mock_generator.call_args
            cmd = args[0]
            assert "openapi-generator-cli" in cmd
            assert "generate" in cmd
            assert "-g" in cmd
            assert "python" in cmd
    
    def test_generate_client_with_config(self, sample_spec, tmp_path, mock_generator):
        """Test generating a client with custom configuration."""
        generator = ClientGenerator()
        generator.spec_processor.spec = sample_spec
        
        config = {
            "packageName": "custom_package",
            "library": "aiohttp",
        }
        
        with mock.patch("builtins.open", mock.mock_open()) as mock_file:
            generator.generate_client(tmp_path, config)
            
            # Check the last call to mock_generator
            args, kwargs = mock_generator.call_args
            cmd = args[0]
            
            # Check that the config options were included
            assert "--additional-properties=packageName=custom_package" in cmd
            assert "--additional-properties=library=aiohttp" in cmd
    
    def test_generate_client_subprocess_error(self, sample_spec, tmp_path):
        """Test handling of subprocess errors during generation."""
        generator = ClientGenerator()
        generator.spec_processor.spec = sample_spec
        
        with mock.patch("subprocess.run") as mock_run:
            mock_result = mock.MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Generation failed"
            mock_run.return_value = mock_result
            
            with mock.patch("builtins.open", mock.mock_open()):
                with pytest.raises(RuntimeError) as excinfo:
                    generator.generate_client(tmp_path)
                assert "Client generation failed" in str(excinfo.value)
    
    def test_validate_generated_client(self, tmp_path):
        """Test validating a generated client."""
        generator = ClientGenerator()
        
        # Create a fake client directory structure
        client_dir = tmp_path / "client"
        os.makedirs(client_dir / "openapi_client")
        (client_dir / "openapi_client" / "__init__.py").touch()
        (client_dir / "openapi_client" / "api_client.py").touch()
        (client_dir / "setup.py").touch()
        
        # Should validate successfully
        assert generator.validate_generated_client(client_dir) is True
    
    def test_validate_generated_client_missing_files(self, tmp_path):
        """Test validating a client with missing files."""
        generator = ClientGenerator()
        
        # Create an incomplete client directory structure
        client_dir = tmp_path / "client"
        os.makedirs(client_dir / "openapi_client")
        (client_dir / "openapi_client" / "__init__.py").touch()
        # Missing api_client.py and setup.py
        
        with pytest.raises(ValueError) as excinfo:
            generator.validate_generated_client(client_dir)
        assert "Invalid client: missing" in str(excinfo.value)
    
    def test_package_client(self, tmp_path, mock_generator):
        """Test packaging a generated client."""
        generator = ClientGenerator()
        
        # Create a fake client directory structure
        client_dir = tmp_path / "client"
        os.makedirs(client_dir / "openapi_client")
        (client_dir / "openapi_client" / "__init__.py").touch()
        (client_dir / "openapi_client" / "api_client.py").touch()
        (client_dir / "setup.py").touch()
        
        # Create a fake dist directory with a wheel
        os.makedirs(client_dir / "dist")
        wheel_path = client_dir / "dist" / "openapi_client-1.0.0-py3-none-any.whl"
        wheel_path.touch()
        
        with mock.patch("os.chdir"):
            result = generator.package_client(client_dir)
            assert result == wheel_path
    
    def test_package_client_with_output_path(self, tmp_path, mock_generator):
        """Test packaging a client with a custom output path."""
        generator = ClientGenerator()
        
        # Create a fake client directory structure
        client_dir = tmp_path / "client"
        os.makedirs(client_dir / "openapi_client")
        (client_dir / "openapi_client" / "__init__.py").touch()
        (client_dir / "openapi_client" / "api_client.py").touch()
        (client_dir / "setup.py").touch()
        
        # Create a fake dist directory with a wheel
        os.makedirs(client_dir / "dist")
        wheel_path = client_dir / "dist" / "openapi_client-1.0.0-py3-none-any.whl"
        wheel_path.touch()
        
        output_path = tmp_path / "output" / "custom.whl"
        
        with mock.patch("os.chdir"), mock.patch("shutil.copy") as mock_copy:
            result = generator.package_client(client_dir, output_path)
            assert result == output_path
            mock_copy.assert_called_once_with(wheel_path, output_path)
    
    def test_package_client_no_wheel(self, tmp_path, mock_generator):
        """Test packaging when no wheel is generated."""
        generator = ClientGenerator()
        
        # Create a fake client directory structure
        client_dir = tmp_path / "client"
        os.makedirs(client_dir / "openapi_client")
        (client_dir / "openapi_client" / "__init__.py").touch()
        (client_dir / "openapi_client" / "api_client.py").touch()
        (client_dir / "setup.py").touch()
        
        # Create an empty dist directory (no wheel)
        os.makedirs(client_dir / "dist")
        
        with mock.patch("os.chdir"):
            with pytest.raises(RuntimeError) as excinfo:
                generator.package_client(client_dir)
            assert "No wheel file found" in str(excinfo.value)