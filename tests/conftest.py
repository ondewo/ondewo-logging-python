import logging

import pytest

from ondewologging.logger import logger_console


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
def log_store():
    m = MockLoggingHandler()
    # logger.addHandler(m)  # TODO: find out why this doesnt work
    yield m


@pytest.fixture(scope="function")
def logger():
    logger = logger_console
    while len(logger.handlers) > 1:
        logger.handlers.pop()
    yield logger
