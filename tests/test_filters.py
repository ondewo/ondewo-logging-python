# Copyright 2021-2024 ONDEWO GmbH
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

from logging import Logger
from typing import (
    Any,
    List,
)

import pytest

from ondewo.logging.filters import ThreadContextFilter
from tests.conftest import MockLoggingHandler


class TestFilters:
    @staticmethod
    @pytest.mark.parametrize(
        "thread_context_filter, message, expected_message",
        [
            # nothing happens when the message is a plain string
            (
                ThreadContextFilter(),
                "hello",
                "hello",
            ),
            (
                ThreadContextFilter(context_dict={"ctx": 123}),
                "hello",
                "hello",
            ),
            # add a context if the message is a dict
            (
                ThreadContextFilter(context_dict={"ctx": 123}),
                {"message": "hello"},
                {"message": "hello", "ctx": 123},
            ),
            (
                ThreadContextFilter(context_dict={"message": "hi"}),
                {"message": "hello"},
                {"message": "hi"},
            ),
        ],
    )
    def test_thread_context_filter(
        log_store: MockLoggingHandler,
        logger: Logger,
        thread_context_filter: ThreadContextFilter,
        message: Any,
        expected_message: Any,
    ) -> None:
        logger.addHandler(log_store)

        logger.info(message)

        logger.addFilter(thread_context_filter)

        logger.info(message)

        logger.removeFilter(thread_context_filter)

        logger.info(message)

        logged_messages: List[str] = log_store.messages["info"]
        assert len(logged_messages) == 3

        for i, logged_message in enumerate(logged_messages):
            try:
                logged_message = eval(logged_message)
            except NameError:
                pass
            if i == 1:
                # message affected with the thread context logger
                assert logged_message == expected_message
            else:
                # message before/after the thread context logger
                assert logged_message == message

        log_store.reset()
