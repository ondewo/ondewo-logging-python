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

import logging.config
import os
import sys

import yaml
from dotenv import load_dotenv

import ondewo.logging.__init__ as file_anchor

load_dotenv()
MODULE_NAME = os.getenv("MODULE_NAME", "")


def import_config():  # type: ignore
    """
    Imports the config from the yaml file. The yaml file is taken relative to this file, so nothing about the python path is assumed.

    :param:
    :return:    logging config as a dictionary
    """
    if os.path.exists("./logging.yaml"):
        config_path = "./logging.yaml"
    else:
        parent = os.path.abspath(os.path.dirname(file_anchor.__file__))
        config_path = "{}/config/logging.yaml".format(parent)

    with open(config_path) as fd:
        conf = yaml.safe_load(fd)

    return conf  # type: ignore


def set_module_name(module_name, conf):  # type: ignore
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

    return conf


def initiate_loggers(conf):  # type: ignore
    """
    Initiate the loggers with the config and return them. Will complain if the module name is not set.

    :param conf:                the config of the logger
    :return:                    the loggers
    """
    logging.config.dictConfig(conf["logging"])

    if not MODULE_NAME:
        logging.warning(
            "NO MODULE NAME WAS GIVEN please give a module name for the fluent logs"
        )

    logger_root = logging.getLogger("root")
    logger_console = logging.getLogger("console")
    logger_debug = logging.getLogger("debug")

    logger = logger_root

    return logger, logger_root, logger_debug, logger_console


def check_python_version():  # type: ignore
    """
    Checks the python version. The python3 logger cant be imported to python 2.

    :param:
    :return:
    """
    if sys.version_info[0] == 3:
        logger_console.error(
            "Looks like you imported the Python2 logger in a Python3 project. Did you mean to do that?"
        )


conf = import_config()
conf = set_module_name(MODULE_NAME, conf)
logger, logger_root, logger_debug, logger_console = initiate_loggers(conf)
check_python_version()
