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

import functools
import time
import traceback
import uuid
from contextlib import ContextDecorator
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Union

from ondewo.logging.constants import CONTEXT, EXCEPTION, FINISH, START
from ondewo.logging.logger import logger_console


@dataclass
class Timer(ContextDecorator):
    """Time your code using a class, context manager, or decorator"""

    name: Optional[str] = None
    message: str = FINISH
    logger: Optional[
        Callable[[Union[str, Dict[str, Any]]], None]
    ] = logger_console.warning
    _start_time: Optional[float] = field(default=None, init=False, repr=False)
    log_arguments: bool = True
    suppress_exceptions: bool = False
    recursive: bool = False
    recurse_depth: int = 0
    argument_max_length: int = 10000

    def __post_init__(self) -> None:
        """Initialization: add timer to dicCallable[[Union[str, Dict[str, Any]]], None]t of timers"""
        if not self.name:
            self.name = str(uuid.uuid4())

    def __call__(self, func: Callable) -> Callable:  # type: ignore
        """
        Decorator which adds a logs timing information for the decorated function.

        :param func:    the function to be decorated
        :return:        the decorator
        """

        @functools.wraps(func)
        def wrapper_timing(*args, **kwargs) -> Any:  # type: ignore
            self.start(func)

            try:
                value: Any = func(*args, **kwargs)
            except Exception as exc:
                trace = traceback.format_exc()
                log_exception(type(exc), next(iter(exc.args), None), trace, func.__name__, self.logger)  # type: ignore
                if not self.suppress_exceptions:
                    self.stop(func.__name__)
                    raise
                value = "An exception occurred!"

            if self.log_arguments:
                log_args_kwargs_results(
                    func, value, self.argument_max_length, self.logger, *args, **kwargs
                )

            self.stop(func.__name__)
            return value

        return wrapper_timing

    def start(self, func: Optional[Callable] = None) -> None:
        """Start a new timer"""
        if func:
            self.logger({"message": START.format(func.__name__)})  # type: ignore
        if self._start_time is not None:
            if self.recursive:
                self.recurse_depth += 1
                self.logger(f"Recursing, depth = {self.recurse_depth}")  # type: ignore
                return
        else:
            self._start_time = time.perf_counter()

    def stop(self, func_name: Optional[str] = None) -> float:
        """Stop the timer, and report the elapsed time"""
        if self.recurse_depth:
            self.recurse_depth -= 1
            if self.recursive:
                return 0.0

        # Calculate elapsed time
        assert self._start_time
        elapsed_time = time.perf_counter() - self._start_time

        # Report elapsed time
        if self.logger:
            self.report(elapsed_time, func_name)

        return elapsed_time

    def report(self, elapsed_time: float, func_name: Optional[str]) -> None:
        name = func_name if func_name else CONTEXT

        try:
            message = self.message.format(elapsed_time, name)
        except IndexError:
            pass

        log: Dict[str, Any] = {
            "message": message,
            "duration": elapsed_time,
            "tags": ["timing"],
        }
        self.logger(log)  # type: ignore

    def __enter__(self) -> "Timer":
        """Start a new timer as a context manager"""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: str, traceback_obj: Any) -> bool:
        """Stop the context manager timer"""
        self.stop()
        if exc_type:
            log_exception(
                exc_type, exc_val, traceback.format_exc(), CONTEXT, self.logger  # type: ignore
            )
        return self.suppress_exceptions


timing = Timer()


def exception_silencing(func: Callable) -> Callable:
    """
    Quietly kills exceptions, logging the minimum.

    :param func:    the function to be decorated
    :return:        the decorator

    """

    @functools.wraps(func)
    def wrapper_error_silent(*args, **kwargs) -> Any:  # type: ignore
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            log_exception(type(exc), next(iter(exc.args), None), None, func.__name__)
            log_args_kwargs_results(func, None, -1, None, *args, **kwargs)
        return None

    return wrapper_error_silent


def exception_handling(func: Callable) -> Callable:
    """
    Hands exceptions on to the logger. This is especially useful in threaded applications where exceptions are often swallowed by the threading demons.

    :param func:    the function to be decorated
    :return:        the decorator

    """

    @functools.wraps(func)
    def wrapper_error(*args, **kwargs) -> Any:  # type: ignore
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            trace = traceback.format_exc()
            log_exception(type(exc), next(iter(exc.args), None), trace, func.__name__)
            log_args_kwargs_results(func, None, -1, None, *args, **kwargs)
        return None

    return wrapper_error


def log_arguments(func: Callable) -> Callable:
    """
    decorate a function to log its arguments and result

    :param func:    the function to be decorated
    :return:        the decorator

    """

    @functools.wraps(func)
    def wrapper_args(*args, **kwargs) -> Any:  # type: ignore
        result = func(*args, **kwargs)
        log_args_kwargs_results(func, result, -1, None, *args, **kwargs)
        return result

    return wrapper_args


def log_exception(
    exc_type: Any,
    exc_val: Optional[str],
    traceback_str: Optional[str],
    function_name: str,
    logger: Callable[[Union[str, Dict[str, Any]]], None] = logger_console.error,
) -> None:
    """
    Formats and logs an exception.
    """
    message = EXCEPTION.format(exc_type, exc_val, function_name)
    log: Dict[str, Any] = {
        "message": message,
        "exception type": exc_type,
        "exception value": exc_val,
        "traceback": traceback_str,
        "tags": ["timing", "exception"],
    }
    logger(log)


def log_args_kwargs_results(  # type: ignore
    func: Callable,
    result: Any,
    argument_max_length: int = -1,
    logger: Optional[
        Callable[[Union[str, Dict[str, Any]]], None]
    ] = logger_console.warning,
    *args,
    **kwargs,
) -> None:
    def truncate_arg(arg_to_truncate: Any) -> str:
        arg_str: str = str(arg_to_truncate)
        if argument_max_length == -1:
            return arg_str
        if len(arg_str) > argument_max_length:
            return arg_str[:argument_max_length] + "<TRUNCATED!>"
        return arg_str

    """
    Format and log all the inputs and outputs of a function
    """
    args_to_log = {truncate_arg(arg) for arg in args}
    kwargs_to_log = {i: truncate_arg(kwargs[i]) for i in kwargs}
    formatted_results: Dict[str, Any] = {
        "function": f"{func.__name__}",
        "args": f"{args_to_log}",
        "kwargs": f"{kwargs_to_log}",
        **kwargs_to_log,
        "result": f"{truncate_arg(result)}",
    }
    if logger:
        logger(
            {
                "message": f"Function arguments log: {formatted_results}",
                **formatted_results,
            }
        )
