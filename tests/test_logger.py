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
import logging
from typing import Dict, Any

import pytest

from ondewo.logging.logger import logger, logger_console, logger_debug, logger_root, flatten_json, CustomLogger


class _Resources:
    test_grpc_request = {"message": 'Got request (type <class \'ondewo.nlu.user_pb2.TestRequest\'>): {'
                                    '"userEmail": "asd@asd.hu", "password": "asa", "stop_phrases_config": {'
                                    '"stop_phrase_files": {"nested": "test"}, "remove_punctuation": false, '
                                    '"active": false}}', "tags": ["test"]}
    json_input = {"userEmail": "asd@asd.hu",
                  "password": "asa",
                  "stop_phrases_config": {"stop_phrase_files": {"nested": "test", "other": ["some", "list"]},
                                          "remove_punctuation": False, "active": False}}


def test_log(log_store):
    CONSOLE_TEXT = "console log"
    logger_console.addHandler(log_store)
    logger_console.debug(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["debug"]
    logger_console.info(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["info"]
    logger_console.warning(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["warning"]
    logger_console.error(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["error"]
    logger_console.critical(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["critical"]

    CONSOLE_TEXT = "debug log"
    logger_debug.addHandler(log_store)
    logger_debug.debug(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["debug"]
    logger_debug.info(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["info"]
    logger_debug.warning(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["warning"]
    logger_debug.error(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["error"]
    logger_debug.critical(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["critical"]

    CONSOLE_TEXT = "root log"
    logger_root.addHandler(log_store)
    logger_root.debug(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["debug"]
    logger_root.info(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["info"]
    logger_root.warning(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["warning"]
    logger_root.error(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["error"]
    logger_root.critical(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["critical"]

    assert len(log_store.messages["critical"]) == 3
    log_store.reset()
    assert len(log_store.messages["critical"]) == 0

    CONSOLE_TEXT = "root log 2"
    logger.addHandler(log_store)
    logger.debug(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["debug"]
    logger.info(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["info"]
    logger.warning(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["warning"]
    logger.error(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["error"]
    logger.critical(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["critical"]


def test_level_manipulation(log_store):
    CONSOLE_TEXT = "console log"
    logger_console.addHandler(log_store)
    logger_console.debug(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["debug"]

    logger_console.setLevel(logging.INFO)
    log_store.reset()
    assert len(log_store.messages["debug"]) == 0

    logger_console.debug(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["debug"]
    logger_console.info(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["info"]

    logger_console.setLevel(logging.WARN)
    log_store.reset()
    assert len(log_store.messages["info"]) == 0

    logger_console.debug(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["debug"]
    logger_console.info(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["info"]
    logger_console.warning(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["warning"]

    logger_console.setLevel(logging.ERROR)
    log_store.reset()
    assert len(log_store.messages["warning"]) == 0

    logger_console.debug(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["debug"]
    logger_console.info(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["info"]
    logger_console.warning(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["warning"]
    logger_console.error(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["error"]

    logger_console.setLevel(logging.CRITICAL)
    log_store.reset()
    assert len(log_store.messages["error"]) == 0

    logger_console.debug(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["debug"]
    logger_console.info(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["info"]
    logger_console.warning(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["warning"]
    logger_console.error(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["error"]
    logger_console.critical(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["critical"]

    logger_console.setLevel(logging.CRITICAL + 1)
    log_store.reset()
    assert len(log_store.messages["error"]) == 0

    logger_console.debug(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["debug"]
    logger_console.info(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["info"]
    logger_console.warning(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["warning"]
    logger_console.error(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["error"]
    logger_console.critical(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["critical"]


def test_handler_level_manipulation(log_store):
    CONSOLE_TEXT = "console log"
    logger_console.setLevel(logging.DEBUG)
    logger_console.addHandler(log_store)
    logger_console.debug(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["debug"]

    for handler in logger_console.handlers:
        handler.setLevel(logging.INFO)
    log_store.reset()
    assert len(log_store.messages["debug"]) == 0

    logger_console.debug(CONSOLE_TEXT)
    assert CONSOLE_TEXT not in log_store.messages["debug"]
    logger_console.info(CONSOLE_TEXT)
    assert CONSOLE_TEXT in log_store.messages["info"]


def test_cai_grpc_converter(logger, log_store):
    condition_one: str = "'stop_phrases_config|stop_phrase_files': '<TRUNCATED!>'"
    condition_two: str = "'stop_phrases_config|stop_phrase_files|nested': 'test'"
    logger.addHandler(log_store)
    logger.grpc({"message": "Test log", "tags": ["test_tag"]})
    for log in log_store.messages["grpc"]:
        assert "{'message': 'Test log', 'tags': ['test_tag']}" in log
    log_store.reset()

    logger.grpc(_Resources.test_grpc_request, max_level=2)
    for log in log_store.messages["grpc"]:
        assert condition_one in log
        assert condition_two not in log
        assert "'tags': ['test', 'grpc']}" in log
    log_store.reset()

    logger.grpc(_Resources.test_grpc_request, max_level=3)
    for log in log_store.messages["grpc"]:
        assert condition_one not in log
        assert condition_two in log
        assert "'tags': ['test', 'grpc']}" in log
    log_store.reset()

    logger.grpc(_Resources.test_grpc_request)
    for log in log_store.messages["grpc"]:
        assert condition_one not in log
        assert condition_two in log
        assert "'tags': ['test', 'grpc']}" in log

    # not grpc logger
    logger.info(_Resources.test_grpc_request)
    for log in log_store.messages["info"]:
        assert "original" not in log
        assert "'tags': ['test']}" in log
        assert "'tags': ['test', 'grpc']}" not in log


@pytest.mark.parametrize(
    'json_input, expected, max_level',
    [
        (
                _Resources.json_input,
                {},
                0
        ),
        (
                _Resources.json_input,
                {'password': 'asa',
                 'stop_phrases_config': '<TRUNCATED!>',
                 'userEmail': 'asd@asd.hu'},
                1
        ),
        (
                _Resources.json_input,
                {'password': 'asa',
                 'stop_phrases_config|active': False,
                 'stop_phrases_config|remove_punctuation': False,
                 'stop_phrases_config|stop_phrase_files': '<TRUNCATED!>',
                 'userEmail': 'asd@asd.hu'},
                2
        ),
        (
                _Resources.json_input,
                {'password': 'asa',
                 'stop_phrases_config|active': False,
                 'stop_phrases_config|remove_punctuation': False,
                 'stop_phrases_config|stop_phrase_files|nested': 'test',
                 'stop_phrases_config|stop_phrase_files|other': ['some', 'list'],
                 'userEmail': 'asd@asd.hu'},
                3
        )
    ]
)
def test_flatten_json(json_input: Dict[Any, Any], expected: Dict[Any, Any], max_level: int) -> None:
    if max_level == 0:
        with pytest.raises(AssertionError):
            flatten_json(json_input, max_level=max_level)
    else:
        result: Dict[Any, Any] = flatten_json(json_input, max_level=max_level)
        assert result == expected


@pytest.mark.parametrize(
    'input_string, expected',
    [
        (
                _Resources.test_grpc_request['message'],
                'ondewo.nlu.user_pb2.TestRequest'
        ),
        (
                'invalid string value',
                ''
        )
    ]
)
def test_extract_grpc_request_class(input_string: str, expected: str) -> None:
    if input_string == 'invalid string value':
        with pytest.raises(AssertionError):
            CustomLogger.extract_grpc_request_class(input_string)
    else:
        result: str = CustomLogger.extract_grpc_request_class(input_string)
        assert result == expected


def test_extract_grpc_message() -> None:
    expected: str = json.loads('{"userEmail": "asd@asd.hu", "password": "asa", '
                               '"stop_phrases_config|stop_phrase_files|nested": "test", '
                               '"stop_phrases_config|remove_punctuation": false, '
                               '"stop_phrases_config|active": false}')
    result: Dict = CustomLogger.extract_grpc_message(_Resources.test_grpc_request['message'], {})
    assert result == expected
