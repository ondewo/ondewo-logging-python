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
import re
from logging import Logger
from multiprocessing.pool import ThreadPool
from threading import Thread, get_ident
from time import sleep
from typing import Any, Callable, Dict, List, Set, Union

import pytest

from ondewo.logging.constants import CONTEXT
from ondewo.logging.decorators import (
    ThreadContextLogger,
    Timer,
    exception_handling,
    exception_silencing,
    timing,
)
from ondewo.logging.logger import logger_console
from tests.conftest import MockLoggingHandler


def test_timer(log_store, logger):
    @Timer()
    def timer_function():
        sleep(0.01)

    logger.addHandler(log_store)
    timer_function()
    assert log_store.count_levels("warning") == 3

    @timing
    def timing_function():
        sleep(0.01)

    timer_function()
    assert log_store.count_levels("warning") == 6

    with Timer():
        sleep(0.01)
    assert log_store.count_levels("warning") == 7

    with timing:
        sleep(0.01)
    assert log_store.count_levels("warning") == 8


def test_timer_messages(log_store, logger):
    MAGIC_WORD = "abracadabra"
    TIMER_MESSAGE = MAGIC_WORD

    @Timer(message=TIMER_MESSAGE)
    def timer_function():
        sleep(0.01)

    logger.addHandler(log_store)
    assert log_store.is_empty()
    assert not log_store.count_levels("warning")
    timer_function()
    all_messages = " ".join(log_store.messages["warning"])
    assert MAGIC_WORD in all_messages

    log_store.reset()
    assert log_store.is_empty()

    with Timer(message=TIMER_MESSAGE):
        sleep(0.01)
    all_messages = " ".join(log_store.messages["warning"])
    assert MAGIC_WORD in all_messages

    MAGIC_WORD = "abracadabra"
    TIMER_MESSAGE = MAGIC_WORD + " {}"

    @Timer(message=TIMER_MESSAGE)
    def timer_function():
        sleep(0.01)

    log_store.reset()
    assert log_store.is_empty()
    timer_function()
    all_messages = " ".join(log_store.messages["warning"])
    assert MAGIC_WORD in all_messages
    assert re.findall(r"\d", all_messages)

    log_store.reset()
    assert log_store.is_empty()

    with Timer(message=TIMER_MESSAGE):
        sleep(0.01)
    all_messages = " ".join(log_store.messages["warning"])
    assert MAGIC_WORD in all_messages
    assert re.findall(r"\d", all_messages)

    MAGIC_WORD = "abracadabra"
    TIMER_MESSAGE = MAGIC_WORD + " {}" + " {}"

    @Timer(message=TIMER_MESSAGE)
    def function_name():
        sleep(0.01)

    log_store.reset()
    assert log_store.is_empty()
    function_name()
    all_messages = " ".join(log_store.messages["warning"])
    assert "function_name" in all_messages
    assert re.findall(r"\d", all_messages)

    with Timer(message=TIMER_MESSAGE):
        sleep(0.01)
    all_messages = " ".join(log_store.messages["warning"])
    assert CONTEXT in all_messages
    assert re.findall(r"\d", all_messages)


def test_timer_level(log_store, logger):
    logger.addHandler(log_store)
    assert log_store.is_empty()

    @Timer(logger=logger.debug)
    def timer_function():
        sleep(0.01)

    assert not log_store.count_levels("debug")
    timer_function()
    assert log_store.count_levels("debug")

    @Timer(logger=logger.info)
    def timer_function():
        sleep(0.01)

    assert not log_store.count_levels("info")
    timer_function()
    assert log_store.count_levels("info")

    log_store.reset()

    @Timer(logger=logger.warning)
    def timer_function():
        sleep(0.01)

    assert not log_store.count_levels("warning")
    timer_function()
    assert log_store.count_levels("warning")

    @Timer(logger=logger.error)
    def timer_function():
        sleep(0.01)

    assert not log_store.count_levels("error")
    timer_function()
    assert log_store.count_levels("error")

    @Timer(logger=logger.critical)
    def timer_function():
        sleep(0.01)

    assert not log_store.count_levels("critical")
    timer_function()
    assert log_store.count_levels("critical")

    log_store.reset()
    assert log_store.is_empty()

    assert not log_store.count_levels("debug")
    with Timer(logger=logger.debug):
        sleep(0.01)
    assert log_store.count_levels("debug")


def test_exception_handling(log_store, logger):
    logger.addHandler(log_store)
    short_list = [1, 2]
    big_index = 3

    @exception_handling
    def error_function():
        short_list[big_index]

    assert log_store.is_empty()
    error_function()
    assert not log_store.is_empty()

    @exception_silencing
    def error_function():
        short_list[big_index]

    log_store.reset()
    assert log_store.is_empty()
    error_function()
    assert not log_store.is_empty()

    @exception_silencing
    def error_function():
        raise Exception()

    log_store.reset()
    assert log_store.is_empty()
    error_function()
    assert not log_store.is_empty()

    @exception_handling
    def error_function():
        raise Exception()

    log_store.reset()
    assert log_store.is_empty()
    error_function()
    assert not log_store.is_empty()

    @Timer(suppress_exceptions=True)
    def error_function():
        short_list[big_index]

    log_store.reset()
    assert log_store.is_empty()
    error_function()
    assert not log_store.is_empty()


def test_timer_depth(log_store, logger):
    @Timer()
    def timer_function(depth=0):
        sleep(0.01)
        if not depth:
            timer_function(depth=depth + 1)

    @Timer()
    def timer_function_recursive(depth=0):
        if not depth > 0:
            timer_function_recursive(depth=depth + 1)
        sleep(0.01)

    logger.addHandler(log_store)
    assert log_store.is_empty()
    timer_function_recursive()
    all_messages = " ".join(log_store.messages["warning"])
    assert "Recursing" not in all_messages

    log_store.reset()
    assert log_store.is_empty()

    @Timer(recursive=True)
    def timer_function_recursive(depth=0):
        if not depth > 0:
            timer_function_recursive(depth=depth + 1)
        sleep(0.01)

    timer_function_recursive()
    all_messages = " ".join(log_store.messages["warning"])
    assert "Recursing" in all_messages


@Timer(logger=logger_console.info)
def concat_two_strings(a: str, b: str) -> str:
    return a + b


@Timer(logger=logger_console.info)
def add_two_integers(a: int, b: int) -> int:
    return a + b


@Timer(logger=logger_console.info, argument_max_length=3)
def concat_two_strings_long(a: str, b: str) -> str:
    return a + b


@Timer(logger=logger_console.info, argument_max_length=-1)
def concat_two_strings_length_minus_one(a: str, b: str) -> str:
    return a + b


@pytest.mark.parametrize(
    "function, param_a, param_b, assert_args, assert_kwargs",
    [
        (
            concat_two_strings,
            "dog",
            "cat",
            ["'dog'", "'cat'", "'result': 'dogcat'"],
            ["'a': 'dog'", "'b': 'cat'", "'result': 'dogcat'"],
        ),
        (
            add_two_integers,
            1,
            2,
            ["'1'", "'2'", "'result': '3'"],
            ["'a': '1'", "'b': '2'", "'result': '3'"],
        ),
        (
            concat_two_strings_long,
            "a",
            "long",
            ["'a'", "'lon<TRUNCATED!>'", "'result': 'alo<TRUNCATED!>'"],
            ["'a': 'a'", "'b': 'lon<TRUNCATED!>'", "'result': 'alo<TRUNCATED!>'"],
        ),
        (
            concat_two_strings_length_minus_one,
            "doglong",
            "catlong",
            ["'doglong'", "'catlong'", "'result': 'doglongcatlong'"],
            ["'a': 'doglong'", "'b': 'catlong'", "'result': 'doglongcatlong'"],
        ),
    ],
    ids=[
        "Param is a string",
        "Param is not a string",
        "String is too long",
        "Max length is -1",
    ],
)
def test_length_filter(
    log_store: MockLoggingHandler,
    logger: Logger,
    function: Callable,
    param_a: Union[str, int],
    param_b: Union[str, int],
    assert_args: List[str],
    assert_kwargs: List[str],
) -> None:
    logger.addHandler(log_store)

    # args
    function(param_a, param_b)
    all_messages = " ".join(log_store.messages["info"])
    for assert_arg in assert_args:
        assert assert_arg in all_messages
    log_store.reset()
    # kwargs
    function(a=param_a, b=param_b)
    all_messages = " ".join(log_store.messages["info"])
    for assert_kwarg in assert_kwargs:
        assert assert_kwarg in all_messages
    log_store.reset()


@Timer()
def concat_two_strings_warning(a: str, b: str) -> str:
    return a + b


def test_length_filter_logger_default_warning(log_store, logger) -> None:
    logger.addHandler(log_store)
    param_a: str = "dog"
    param_b: str = "cat"
    assert_args: List[str] = ["'dog'", "'cat'", "'result': 'dogcat'"]
    assert_kwargs: List[str] = ["'a': 'dog'", "'b': 'cat'", "'result': 'dogcat'"]

    # args
    concat_two_strings_warning(param_a, param_b)
    all_messages = " ".join(log_store.messages["warning"])
    for assert_arg in assert_args:
        assert assert_arg in all_messages
    log_store.reset()
    # kwargs
    concat_two_strings_warning(a=param_a, b=param_b)
    all_messages = " ".join(log_store.messages["warning"])
    for assert_kwarg in assert_kwargs:
        assert assert_kwarg in all_messages
    log_store.reset()


def test_nested_functions(log_store, logger) -> None:
    logger.addHandler(log_store)

    @Timer()
    def function_a():
        sleep(0.01)

    @Timer()
    def function_b():
        function_a()
        sleep(0.01)

    function_b()

    all_messages = " ".join(log_store.messages["warning"])
    assert all_messages.count("Elapsed time") == 2


def test_function_repeated(log_store: MockLoggingHandler, logger: Logger) -> None:
    logger.addHandler(log_store)

    @Timer()
    def function():
        sleep(0.01)

    for _ in range(10):
        function()

    durations: List[float] = []
    for message in log_store.messages["warning"]:
        message_dict: Dict[str, Any] = eval(message)
        if "duration" in message_dict:
            durations.append(message_dict["duration"])
    assert all(0.011 == pytest.approx(duration, abs=0.001) for duration in durations)


def test_function_concurrent(log_store: MockLoggingHandler, logger: Logger) -> None:
    logger.addHandler(log_store)

    @Timer()
    def function():
        sleep(0.01)

    n_threads: int = 10
    with ThreadPool(processes=n_threads) as pool:
        pool.starmap(function, [[] for _ in range(n_threads)])

    durations: List[float] = []
    for message in log_store.messages["warning"]:
        message_dict: Dict[str, Any] = eval(message)
        if "duration" in message_dict:
            durations.append(message_dict["duration"])
    assert all(0.011 == pytest.approx(duration, abs=0.005) for duration in durations)


def test_timer_as_context_manager(log_store, logger) -> None:
    logger.addHandler(log_store)
    with Timer(logger=logger_console.warning):
        concat_two_strings_warning("a", "b")
    all_messages = " ".join(log_store.messages["warning"])
    assert "exception" not in all_messages
    log_store.reset()

    with Timer(logger=logger_console.warning, suppress_exceptions=True):
        raise Exception
    all_messages = " ".join(log_store.messages["warning"])
    assert "exception" in all_messages
    log_store.reset()


class TestThreadContextLogger:
    @staticmethod
    @pytest.mark.parametrize(
        "message, expected_message",
        [
            # nothing happens when the message is a plain string
            (
                "hello",
                "hello",
            ),
            # add a context if the message is a dict
            (
                {"message": "hello"},
                {"message": "hello", "ctx": 123},
            ),
        ],
    )
    @pytest.mark.parametrize(
        "thread_context_logger_type", ["context_manager", "decorator"]
    )
    def test_thread_context_logger(
        log_store: MockLoggingHandler,
        logger: Logger,
        thread_context_logger_type: str,
        message: Any,
        expected_message: Any,
    ) -> None:
        logger.addHandler(log_store)

        thread_context_logger: ThreadContextLogger = ThreadContextLogger(
            logger=logger,
            context_dict={"ctx": 123},
        )

        @thread_context_logger
        def function(msg: str) -> None:
            logger.info(msg)

        logger.info(message)

        if thread_context_logger_type == "context_manager":
            with thread_context_logger:
                logger.info(message)
        elif thread_context_logger_type == "decorator":
            function(msg=message)

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

    @staticmethod
    def test_thread_context_logger_in_multiple_threads(
        log_store: MockLoggingHandler,
        logger: Logger,
    ) -> None:
        logger.addHandler(log_store)

        def function(ctx: int) -> None:
            with ThreadContextLogger(logger=logger, context_dict={"ctx": ctx}):
                logger.info({"message": "start"})

                sub_thread: Thread = Thread(
                    target=lambda: logger.info({"message": "continue"}),
                    name=f"sub-thread-{get_ident()}",
                )
                sub_thread.start()
                sub_thread.join()

                logger.info({"message": "end"})

        n_threads: int = 10
        with ThreadPool(processes=n_threads) as pool:
            pool.map(function, range(n_threads))

        messages: List[Dict[str, Any]] = [
            eval(message) for message in log_store.messages["info"]
        ]
        for i in range(n_threads):
            messages_ctx: Set[str] = {
                message["message"] for message in messages if message["ctx"] == i
            }
            assert messages_ctx == {"start", "continue", "end"}

        log_store.reset()
