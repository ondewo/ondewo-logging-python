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
from collections import defaultdict
from contextlib import ContextDecorator
from dataclasses import dataclass, field
from logging import Filter, Logger
from threading import get_ident
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from ondewo.logging.constants import CONTEXT, EXCEPTION, FINISH, START
from ondewo.logging.filters import ThreadContextFilter
from ondewo.logging.logger import logger_console

TF = TypeVar("TF", bound=Callable[..., Any])


@dataclass
class Timer(ContextDecorator):
    """Time your code using a class, context manager, or decorator"""

    name: str = field(default_factory=lambda: str(uuid.uuid4()))
    message: str = FINISH
    logger: Callable[..., None] = logger_console.warning
    _start_times: Dict[int, float] = field(default_factory=dict, init=False, repr=False)
    log_arguments: bool = True
    suppress_exceptions: bool = False
    recursive: bool = False
    recurse_depths: Dict[int, float] = field(default_factory=lambda: defaultdict(float))
    argument_max_length: int = 10000

    def __call__(self, func: TF) -> TF:
        """Decorator which adds a logs timing information for the decorated function.

        Args
            func: the function to be decorated

        Returns:
            the decorator
        """

        @functools.wraps(func)
        def wrapper_timing(*args, **kwargs) -> Any:
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

        return wrapper_timing  # type: ignore

    def start(self, func: Optional[TF] = None) -> None:
        """Start a new timer"""
        thread_id: int = get_ident()
        if func:
            self.logger({"message": START.format(func.__name__, thread_id)})
        if thread_id in self._start_times:
            if self.recursive:
                self.recurse_depths[thread_id] += 1
                self.logger(f"Recursing, depth = {self.recurse_depths[thread_id]}")
                return
        else:
            self._start_times[thread_id] = time.perf_counter()

    def stop(self, func_name: Optional[str] = None) -> float:
        """Stop the timer, and report the elapsed time"""
        thread_id: int = get_ident()

        if self.recurse_depths[thread_id]:
            self.recurse_depths[thread_id] -= 1
            if self.recursive:
                return 0.0

        # Calculate elapsed time
        if thread_id in self._start_times:
            elapsed_time = time.perf_counter() - self._start_times[thread_id]

            # reset the start time
            del self._start_times[thread_id]
        else:
            elapsed_time = 0.0

        # Report elapsed time
        if self.logger:
            self.report(
                elapsed_time=elapsed_time, func_name=func_name, thread_id=thread_id
            )

        return elapsed_time

    def report(
        self,
        elapsed_time: float,
        func_name: Optional[str] = None,
        thread_id: Optional[int] = None,
    ) -> None:
        name: str = func_name or CONTEXT

        try:
            message = self.message.format(elapsed_time, name, thread_id)
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
    func: TF,
    result: Any,
    argument_max_length: int = -1,
    logger: Optional[Callable[..., None]] = logger_console.warning,
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


class ThreadContextLogger(ContextDecorator):
    """Add per-thread context information using a class, context manager or decorator."""

    def __init__(
        self,
        context_dict: Optional[Dict[str, Any]] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        """

        Args:
            context_dict: optional context information to add to the logs from the current thread
            logger: optional logger to add the information to (be default the global logger_console)
        """
        self.logger: Logger = logger or logger_console
        self.filter: Filter = ThreadContextFilter(context_dict=context_dict)

    def __enter__(self) -> None:
        """Add the filter to the logger when entering the context."""
        self.logger.addFilter(self.filter)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Remove the filter from the logger when leaving the context."""
        self.logger.removeFilter(self.filter)
