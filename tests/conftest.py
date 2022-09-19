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

import logging
from typing import Iterator

import pytest

from ondewo.logging.logger import logger_debug


class MockLoggingHandler(logging.Handler):
    """Mock logging handler to check for expected logs."""

    def __init__(self, *args, **kwargs):
        self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record.getMessage())

    def reset(self):
        self.messages = {
            "debug": [],
            "info": [],
            "warning": [],
            "error": [],
            "critical": [],
            "grpc": [],
        }

    def count_levels(self, level=None):
        if level:
            return len(self.messages[level])
        else:
            return sum(len(self.messages[key]) for key in self.messages.keys())

    def is_empty(self):
        return not bool(self.count_levels())


@pytest.fixture(scope="function")
def log_store() -> Iterator[MockLoggingHandler]:
    m = MockLoggingHandler()
    # logger.addHandler(m)  # TODO: find out why this doesnt work
    yield m


@pytest.fixture(scope="function")
def logger() -> Iterator[logging.Logger]:
    logger = logger_debug
    while len(logger.handlers) > 1:
        logger.handlers.pop()
    yield logger
