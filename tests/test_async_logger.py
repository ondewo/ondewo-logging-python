import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest
import yaml

from ondewo.logging.async_logger import (AsyncCustomLogger,
                                         check_python_version, create_logs,
                                         import_config, initiate_loggers,
                                         set_module_name)


@pytest.mark.asyncio
async def test_import_config_exists_at_root(tmp_path: Path) -> None:
    """Tests if the config is loaded correctly when 'logging.yaml' exists at the root."""
    config_data: Dict[str, Any] = {"level": "INFO", "format": "%(asctime)s - %(levelname)s - %(message)s"}
    config_file: Path = tmp_path / "logging.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Change the current working directory to tmp_path for the test
    os.chdir(tmp_path)
    try:
        loaded_config: Dict[str, Any] = await import_config()
        assert loaded_config == config_data
    finally:
        # Change back to the original working directory
        os.chdir(Path(__file__).parent)


@pytest.mark.asyncio
async def test_import_config_exists_in_subdir(tmp_path: Path) -> None:
    """Tests if the config is loaded correctly when 'logging.yaml' exists in the 'config' subdirectory."""
    config_data: Dict[str, Any] = {"handlers": {"console": {"level": "DEBUG"}}}
    config_dir: Path = tmp_path / "config"
    config_dir.mkdir()
    config_file: Path = config_dir / "logging.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Patch __file__ to simulate the module being in tmp_path
    with patch("ondewo.logging.async_logger.__file__", str(tmp_path / "your_module.py")):
        loaded_config: Dict[str, Any] = await import_config()
        assert loaded_config == config_data


@pytest.mark.asyncio
async def test_import_config_not_found(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Tests the behavior when the 'logging.yaml' file is not found."""
    # Patch __file__ to simulate the module being in tmp_path
    with patch("ondewo.logging.async_logger.__file__", str(tmp_path / "your_module.py")):
        loaded_config: Dict[str, Any] = await import_config()
        assert loaded_config == {}
        captured = capsys.readouterr()
        assert f"Config file not found: {tmp_path / 'config' / 'logging.yaml'}" in captured.out


@pytest.mark.asyncio
async def test_import_config_empty_file_root(tmp_path: Path) -> None:
    """Tests the behavior when 'logging.yaml' at the root is empty."""
    config_file: Path = tmp_path / "logging.yaml"
    config_file.write_text("")
    os.chdir(tmp_path)
    try:
        loaded_config: Dict[str, Any] = await import_config()
        assert loaded_config == {}
    finally:
        os.chdir(Path(__file__).parent)


@pytest.mark.asyncio
async def test_import_config_empty_file_subdir(tmp_path: Path) -> None:
    """Tests the behavior when 'logging.yaml' in the subdirectory is empty."""
    config_dir: Path = tmp_path / "config"
    config_dir.mkdir()
    config_file: Path = config_dir / "logging.yaml"
    config_file.write_text("")
    with patch("ondewo.logging.async_logger.__file__", str(tmp_path / "your_module.py")):
        loaded_config: Dict[str, Any] = await import_config()
        assert loaded_config == {}


@pytest.mark.asyncio
async def test_import_config_invalid_yaml_root(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Tests the behavior when 'logging.yaml' at the root contains invalid YAML."""
    invalid_yaml: str = "this is not valid yaml: -"
    config_file: Path = tmp_path / "logging.yaml"
    config_file.write_text(invalid_yaml)
    os.chdir(tmp_path)
    try:
        loaded_config: Dict[str, Any] = await import_config()
        assert loaded_config == {}
        captured = capsys.readouterr()
        assert "Error parsing YAML file" in captured.out
    finally:
        os.chdir(Path(__file__).parent)


@pytest.mark.asyncio
async def test_set_module_name():
    conf = {"logging": {"formatters": {"fluent_debug": {"format": {}}, "fluent_console": {"format": {}}}}}
    module_name = "test_module"
    git_repo_name = "test_repo"
    docker_image_name = "test_image"

    updated_conf = await set_module_name(module_name, git_repo_name, docker_image_name, conf)
    assert updated_conf["logging"]["formatters"]["fluent_debug"]["format"]["module_name"] == module_name
    assert updated_conf["logging"]["formatters"]["fluent_console"]["format"]["git_repo_name"] == git_repo_name


@pytest.mark.asyncio
async def test_initiate_loggers():
    conf = {"logging": {"version": 1, "loggers": {"root": {}, "console": {}, "debug": {}}}}
    logger_root, logger_console, logger_debug = await initiate_loggers(conf)
    assert isinstance(logger_root, logging.Logger)
    assert isinstance(logger_console, logging.Logger)
    assert isinstance(logger_debug, logging.Logger)


@pytest.mark.asyncio
async def test_check_python_version(caplog):
    logger = logging.getLogger("test_logger")
    await check_python_version(logger)
    if sys.version_info[0] == 2:
        assert "Python 2 is not supported" in caplog.text


@pytest.mark.asyncio
async def test_create_logs():
    logger_root, logger_console, logger_debug = await create_logs()
    assert isinstance(logger_root, logging.Logger)
    assert isinstance(logger_console, logging.Logger)
    assert isinstance(logger_debug, logging.Logger)


@pytest.mark.asyncio
async def test_async_custom_logger_grpc():
    logger = AsyncCustomLogger("test_logger")
    message_dict = {"message": "Test GRPC message"}
    await logger.grpc(message_dict)
    assert logger.isEnabledFor(AsyncCustomLogger.GRPC_LEVEL_NUM)
