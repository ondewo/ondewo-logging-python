import asyncio
import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import (
    Any,
    Dict,
    Optional,
    Tuple,
)

import aiofiles
import yaml
from dotenv import load_dotenv

from ondewo.logging.decorators import AsyncTimer

load_dotenv()
MODULE_NAME: str = os.getenv("MODULE_NAME", "")
GIT_REPO_NAME: str = os.getenv("GIT_REPO_NAME", "")
DOCKER_IMAGE_NAME: str = os.getenv("DOCKER_IMAGE_NAME", "")


class AsyncCustomLogger(logging.Logger):
    GRPC_LEVEL_NUM = 25
    logging.addLevelName(GRPC_LEVEL_NUM, "GRPC")

    async def grpc(self, message_dict: Dict[str, Any], *args, **kwargs) -> None:
        if self.isEnabledFor(self.GRPC_LEVEL_NUM):
            await asyncio.sleep(0)  # Simulate async processing
            super().log(self.GRPC_LEVEL_NUM, message_dict, *args, **kwargs)


async def import_config() -> Dict[str, Any]:
    """
    Asynchronously imports the logging configuration from a YAML file.

    The function first checks for 'logging.yaml' in the current directory.
    If not found, it looks in a 'config' subdirectory relative to the
    location of the current file.

    Returns:
        A dictionary containing the loaded configuration. Returns an empty
        dictionary if the file is not found or if there's an error parsing
        the YAML.
    """
    config_path: Path

    if os.path.exists("./logging.yaml"):
        config_path = Path("./logging.yaml")
    else:
        parent: Path = Path(__file__).resolve().parent
        config_path = parent / "config" / "logging.yaml"

    conf: Dict[str, Any] = {}

    try:
        async with aiofiles.open(config_path, mode="r") as fd:
            content: str = await fd.read()
            try:
                loaded_config: Optional[Dict[str, Any]] = yaml.safe_load(content)
                conf = loaded_config if loaded_config is not None else {}
            except yaml.YAMLError as e:
                print(f"Error parsing YAML file: {e}")
                conf = {}
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")

    return conf


async def set_module_name(
    module_name: str,
    git_repo_name: str,
    docker_image_name: str,
    conf: Dict[str, Any]
) -> Dict[str, Any]:
    conf["logging"]["formatters"]["fluent_debug"]["format"]["module_name"] = module_name
    conf["logging"]["formatters"]["fluent_debug"]["format"]["git_repo_name"] = git_repo_name
    conf["logging"]["formatters"]["fluent_debug"]["format"]["docker_image_name"] = docker_image_name

    conf["logging"]["formatters"]["fluent_console"]["format"]["module_name"] = module_name
    conf["logging"]["formatters"]["fluent_console"]["format"]["git_repo_name"] = git_repo_name
    conf["logging"]["formatters"]["fluent_console"]["format"]["docker_image_name"] = docker_image_name

    return conf


async def initiate_loggers(conf: Dict[str, Any]) -> Tuple[logging.Logger, ...]:
    logging.setLoggerClass(AsyncCustomLogger)
    logging.config.dictConfig(conf["logging"])

    if not GIT_REPO_NAME:
        logging.warning("NO GIT REPO NAME WAS GIVEN. Please set the GIT_REPO_NAME env var.")
    if not DOCKER_IMAGE_NAME:
        logging.warning("NO DOCKER IMAGE NAME WAS GIVEN. Please state the docker image for the logs.")
    if not MODULE_NAME:
        logging.warning("NO MODULE NAME WAS GIVEN. Please provide a module name for the logs.")
    if not os.path.exists("./logging.yaml"):
        logging.info("No logging.yaml in the root of the project, using the default config.")

    logger_root: logging.Logger = logging.getLogger("root")
    logger_console: logging.Logger = logging.getLogger("console")
    logger_debug: logging.Logger = logging.getLogger("debug")

    return logger_root, logger_console, logger_debug


async def check_python_version(logger: logging.Logger) -> None:
    if sys.version_info[0] == 2:
        logger.error("Python 2 is not supported. Please use Python 3.")


async def create_logs(conf: Optional[Dict[str, Any]] = None) -> Tuple[logging.Logger, ...]:
    conf = conf if conf else await import_config()
    conf = await set_module_name(MODULE_NAME, GIT_REPO_NAME, DOCKER_IMAGE_NAME, conf)
    logger_root, logger_console, logger_debug = await initiate_loggers(conf)
    await check_python_version(logger_console)
    return logger_root, logger_console, logger_debug


def sync_create_logs():
    try:
        return asyncio.run(create_logs())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(create_logs())


logger_root, logger_console, logger_debug = sync_create_logs()


# Example usage
async def main():
    logger_root, logger_console, logger_debug = await create_logs()
    logger_console.info("Asynchronous logging system initialized.")

    @AsyncTimer(logger=logger_console.debug, log_arguments=False, message="Test Elapsed: {:0.3f}")
    async def my_test_function(val: int) -> int:
        await asyncio.sleep(0.01)  # Simulate some work
        logger_console.info(f"Test value: {val}")
        return val * 2

    await my_test_function(5)


if __name__ == "__main__":
    asyncio.run(main())
