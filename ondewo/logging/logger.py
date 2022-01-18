# Copyright 2021 ONDEWO GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging.config
import os
import re
import sys
from typing import Any, Dict, Optional, Tuple

import yaml
from dotenv import load_dotenv

import ondewo.logging.__init__ as file_anchor

load_dotenv()
MODULE_NAME: str = os.getenv("MODULE_NAME", "")
GIT_REPO_NAME: str = os.getenv("GIT_REPO_NAME", "")
DOCKER_IMAGE_NAME: str = os.getenv("DOCKER_IMAGE_NAME", "")


def flatten_json(y: Any, max_level: int = 3) -> Dict:
    output = {}

    def flatten_recursively(node: Any, name: str = "", level: int = 0) -> None:
        assert max_level > 0
        if level < max_level:
            if type(node) is dict:
                for sub_node in node:
                    flatten_recursively(
                        node[sub_node], name + sub_node + "|", level + 1
                    )
            else:
                output[name[:-1]] = node
        else:
            if type(node) is dict:
                output[name[:-1]] = "<TRUNCATED!>"
            else:
                output[name[:-1]] = node

    flatten_recursively(y)
    return output


class CustomLogger(logging.Logger):
    GRPC_LEVEL_NUM = 25
    logging.addLevelName(GRPC_LEVEL_NUM, "GRPC")

    @staticmethod
    def extract_grpc_request_class(msg: str) -> str:
        pattern_request_type = re.compile("\\(type <class '(.*)'>")
        request_type_search_result = pattern_request_type.search(msg)
        assert request_type_search_result
        request_type = request_type_search_result.group(1)
        return request_type

    @staticmethod
    def extract_grpc_message(msg: str, kwargs) -> Dict:  # type: ignore
        extracted: Dict = {}
        grpc_matches = re.findall("{.*}", msg)
        if grpc_matches:
            longest_match = max(grpc_matches)
            grpc_json = json.loads(longest_match)
            if "max_level" in kwargs:
                max_level = kwargs["max_level"]
                extracted = flatten_json(grpc_json, max_level)
            else:
                extracted = flatten_json(grpc_json)
        return extracted

    def grpc(self, message_dict: Dict[str, Any], *args, **kwargs) -> None:  # type: ignore
        if logging.getLogger().isEnabledFor(self.GRPC_LEVEL_NUM):
            message: str = message_dict["message"]
            if "Got request (type <class" in message:
                request_type = CustomLogger.extract_grpc_request_class(message)
                extracted = CustomLogger.extract_grpc_message(message, kwargs)
                to_log = {"original": message, **extracted}
                # Add request type
                if request_type:
                    to_log["request_type"] = request_type
                    # Update tags with 'grpc'
                    to_log["tags"] = (
                        message_dict["tags"] + ["grpc"]
                        if "tags" in message_dict
                        else ["grpc"]
                    )
                if "max_level" in kwargs:
                    kwargs.pop("max_level")
                return super(CustomLogger, self).log(
                    self.GRPC_LEVEL_NUM, to_log, *args, **kwargs
                )
            else:
                if "max_level" in kwargs:
                    kwargs.pop("max_level")
                return super(CustomLogger, self).log(
                    self.GRPC_LEVEL_NUM, message_dict, *args, **kwargs
                )


def import_config() -> Dict[str, Any]:
    """
    Imports the config from the yaml file. The yaml file is taken relative to this file, so nothing about the python path is assumed.

    :param:
    :return:    logging config as a dictionary
    """
    if os.path.exists("/home/ondewo/logging.yaml"):
        config_path: str = "/home/ondewo/logging.yaml"
    else:
        parent: str = os.path.abspath(os.path.dirname(file_anchor.__file__))
        config_path = f"{parent}/config/logging.yaml"

    with open(config_path) as fd:
        conf = yaml.safe_load(fd)

    return conf  # type: ignore


def set_module_name(
    module_name: str, git_repo_name: str, docker_image_name: str, conf: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Sets the module name as given in the env on deployment.

    :param module_name:         the name of the module the logger is running in
    :param conf:                the config of the logger
    :return:                    the config with module name
    """
    conf["logging"]["formatters"]["fluent_console"]["format"][
        "module_name"
    ] = module_name
    conf["logging"]["formatters"]["fluent_debug"]["format"]["module_name"] = module_name
    conf["logging"]["formatters"]["fluent_console"]["format"][
        "git_repo_name"
    ] = git_repo_name
    conf["logging"]["formatters"]["fluent_debug"]["format"][
        "git_repo_name"
    ] = git_repo_name
    conf["logging"]["formatters"]["fluent_console"]["format"][
        "docker_image_name"
    ] = docker_image_name
    conf["logging"]["formatters"]["fluent_debug"]["format"][
        "docker_image_name"
    ] = docker_image_name

    return conf


def initiate_loggers(conf: Dict[str, Any]) -> Tuple[logging.Logger, ...]:
    """
    Initiate the loggers with the config and return them. Will complain if the module name is not set.

    :param conf:                the config of the logger
    :return:                    the loggers
    """
    logging.setLoggerClass(CustomLogger)
    logging.config.dictConfig(conf["logging"])

    if not GIT_REPO_NAME:
        logging.warning(
            "NO GIT REPO NAME WAS GIVEN please set the GIT_REPO_NAME env var\n"
            "   the GIT REPO NAME provides information to the logs\n"
            "   that may be unavailable in the image\n"
            "   it can (and should) be set at the start of the Dockerfile\n"
        )
    if not DOCKER_IMAGE_NAME:
        logging.warning(
            "NO DOCKER IMAGE NAME WAS GIVEN please state the docker image for the fluent logs\n"
        )
    if not MODULE_NAME:
        logging.warning(
            "NO MODULE NAME WAS GIVEN please give a module name for the fluent logs\n"
            "   the MODULE NAME providers information about the environment\n"
            "   such as which deployment the logs are coming from\n"
        )
    if not os.path.exists("./logging.yaml"):
        logging.info(
            "No logging.yaml in the root of the project, using the default config.\n"
        )

    logger_root: logging.Logger = logging.getLogger("root")
    logger_console: logging.Logger = logging.getLogger("console")
    logger_debug: logging.Logger = logging.getLogger("debug")

    logger: logging.Logger = logger_root

    return logger, logger_root, logger_debug, logger_console


def check_python_version(logger: logging.Logger) -> None:
    """
    Checks the python version. The python3 logger cant be imported to python 2.

    :param:
    :return:
    """
    if sys.version_info[0] == 2:
        # this wont actually run because of syntax errors, but functions as a sort of documentation
        logger.error(
            "Looks like you imported the Python3 logger in a Python2 project. Did you mean to do that?"
        )


def create_logs(conf: Optional[Dict[str, Any]] = None) -> Tuple[logging.Logger, ...]:
    """
    Loads, configures and returns logs.

    :param conf:    configuration dictionary, so the loggers can be configured in individual submodules.
    :return:        all the loggers
    """
    conf = conf if conf else import_config()
    conf = set_module_name(MODULE_NAME, GIT_REPO_NAME, DOCKER_IMAGE_NAME, conf)
    logger, logger_root, logger_debug, logger_console = initiate_loggers(conf)
    check_python_version(logger_console)
    return logger, logger_root, logger_debug, logger_console


logger, logger_root, logger_debug, logger_console = create_logs()
