import re
from time import sleep
from typing import List, Union, Callable

import pytest

from ondewologging.constants import CONTEXT
from ondewologging.decorators import Timer, exception_handling, exception_silencing, timing
from ondewologging.logger import logger_console


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
    "function, param_a, param_b, assert_args, assert_kwargs", [
        (
                concat_two_strings,
                "dog",
                "cat",
                ["'dog'", "'cat'", "'result': 'dogcat'"],
                ["'a': 'dog'", "'b': 'cat'", "'result': 'dogcat'"]
        ),
        (
                add_two_integers,
                1,
                2,
                ["'1'", "'2'", "'result': '3'"],
                ["'a': '1'", "'b': '2'", "'result': '3'"]
        ),
        (
                concat_two_strings_long,
                "a",
                "long",
                ["'a'", "'lon<TRUNCATED!>'", "'result': 'alo<TRUNCATED!>'"],
                ["'a': 'a'", "'b': 'lon<TRUNCATED!>'", "'result': 'alo<TRUNCATED!>'"]
        ),
        (
                concat_two_strings_length_minus_one,
                "doglong",
                "catlong",
                ["'doglong'", "'catlong'", "'result': 'doglongcatlong'"],
                ["'a': 'doglong'", "'b': 'catlong'", "'result': 'doglongcatlong'"]
        ),
    ],
    ids=["Param is a string", "Param is not a string", "String is too long", "Max length is -1"],
)
def test_length_filter(
        log_store,
        logger,
        function: Callable,
        param_a: Union[str, int],
        param_b: Union[str, int],
        assert_args: List[str],
        assert_kwargs: List[str]
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


def test_length_filter_logger_default_warning(
        log_store,
        logger
) -> None:
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


def test_nested_functions(
        log_store,
        logger
) -> None:
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
    assert all_messages.count('Elapsed time') == 2


def test_timer_as_context_manager(
        log_store,
        logger
) -> None:
    logger.addHandler(log_store)
    with Timer(logger=logger_console.warning) as time:
        concat_two_strings_warning('a', 'b')
    all_messages = " ".join(log_store.messages["warning"])
    assert 'exception' not in all_messages
    log_store.reset()

    with Timer(logger=logger_console.warning, suppress_exceptions=True) as time:
        raise Exception
    all_messages = " ".join(log_store.messages["warning"])
    assert 'exception' in all_messages
    log_store.reset()
