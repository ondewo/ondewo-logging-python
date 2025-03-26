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
import functools
import inspect
import json
import time
import traceback
import uuid
from collections import defaultdict
from contextlib import ContextDecorator
from dataclasses import (
    dataclass,
    field,
)
from functools import wraps
from inspect import iscoroutinefunction
from logging import (
    Filter,
    Logger,
)
from threading import get_ident
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Optional,
    TypeVar,
    Union,
)

import wrapt

from ondewo.logging.constants import (
    CONTEXT,
    EXCEPTION,
    FINISH,
    START,
)
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

    @wrapt.decorator
    def __call__(self, wrapped: Any, instance: Optional[Any], args: Any, kwargs: Any) -> Any:
        self.start(wrapped, instance, args, kwargs)

        value: Any
        try:
            value = wrapped(*args, **kwargs)
        except Exception as exc:
            trace = traceback.format_exc()
            function_name = getattr(wrapped, '__name__', "UNKNOWN_FUNCTION_NAME")
            log_exception(type(exc), next(iter(exc.args), None), trace, function_name, self.logger)

            if not self.suppress_exceptions:
                self.stop(function_name)
                raise
            value = "An exception occurred!"

        if self.log_arguments:
            log_args_kwargs_results(wrapped, value, self.argument_max_length, self.logger, *args, **kwargs)

        self.stop(wrapped.__name__)
        return value

    def start(
        self,
        func: Optional[wrapt.FunctionWrapper] = None,
        instance: Optional[Any] = None,
        args: Optional[Any] = None,
        kwargs: Optional[Any] = None
    ) -> None:
        """Start a new timer"""
        thread_id: int = get_ident()
        if func:
            function_name: str = "UNKNOWN_FUNCTION_NAME"

            if isinstance(func, wrapt.FunctionWrapper):
                original_func = func.original
                if hasattr(original_func, '__name__'):
                    function_name = original_func.__name__
                elif hasattr(original_func, '__str__'):
                    function_name = str(original_func)
                else:
                    function_name = "UNKNOWN_FUNCTION_NAME"
            else:
                if hasattr(func, '__name__'):
                    function_name = func.__name__
                elif hasattr(func, '__str__'):
                    function_name = str(func)
                else:
                    function_name = "UNKNOWN_FUNCTION_NAME"

            self.logger({"message": START.format(function_name, thread_id)})

        if thread_id in self._start_times:
            if self.recursive:
                self.recurse_depths[thread_id] += 1
                self.logger(f"Recursing, depth = {self.recurse_depths[thread_id]}")
                return
        else:
            self._start_times[thread_id] = time.perf_counter()

    def stop(self, func: Optional[wrapt.FunctionWrapper] = None) -> float:
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
        if self.logger:  # type: ignore
            func_name = None
            if func:
                if isinstance(func, wrapt.FunctionWrapper):
                    original_func = func.original
                    if hasattr(original_func, '__name__'):
                        func_name = original_func.__name__
                    elif hasattr(original_func, '__str__'):
                        func_name = str(original_func)
                else:
                    if hasattr(func, '__name__'):
                        func_name = func.__name__
                    elif hasattr(func, '__str__'):
                        func_name = str(func)

            self.report(elapsed_time=elapsed_time, func_name=func_name, thread_id=thread_id)

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
        except IndexError as index_error:
            print(index_error)
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
            log_exception(exc_type, exc_val, traceback.format_exc(), CONTEXT, self.logger)  # type: ignore
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

            function_name: str = "UNKNOWN_FUNCTION_NAME"
            if hasattr(func, '__name__'):
                function_name = func.__name__
            elif hasattr(func, '__str__'):
                function_name = func.__str__  # type: ignore
            else:
                function_name = "UNKNOWN_FUNCTION_NAME"

            log_exception(type(exc), next(iter(exc.args), None), None, function_name)
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

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Remove the filter from the logger when leaving the context."""
        self.logger.removeFilter(self.filter)


def async_log_exception(logger: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]):
    """
    An asynchronous decorator to log exceptions raised by an async function.

    Args:
        logger: An async function to handle the log record.
    """

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                exc_type = type(e)
                exc_val = e
                tb = traceback.extract_tb(e.__traceback__)
                traceback_str = "".join(traceback.format_list(tb))
                function_name = func.__name__
                log_data = {
                    "tags": ["exception"],
                    "message": str(exc_val),
                    "traceback": traceback_str,
                    "function": function_name,
                    "exception_type": exc_type.__name__,
                    "log_type": "exception",
                }
                await logger(log_data)
                raise  # Re-raise the exception after logging

        return wrapper

    return decorator


def async_log_args_kwargs_results(
    logger: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]],
    argument_max_length: int = 50,
):
    """
    An asynchronous decorator to log arguments, keyword arguments, and the result
    of an async function.

    Args:
        logger: An async function that accepts a dictionary containing
                the log information.
        argument_max_length: The maximum length to represent arguments as strings.
    """

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            signature = inspect.signature(func)
            bound_arguments = signature.bind(*args, **kwargs)
            bound_arguments.apply_defaults()

            formatted_args = {
                name: repr(value)[:argument_max_length]
                for name, value in bound_arguments.arguments.items()
            }
            formatted_kwargs = {
                name: repr(value)[:argument_max_length] for name, value in kwargs.items()
            }

            log_data_before = {
                "message": f"Function called: {func.__name__} with args={json.dumps(formatted_args)}, kwargs={json.dumps(formatted_kwargs)}",
                "function": func.__name__,
                "args": formatted_args,
                "kwargs": formatted_kwargs,
                "log_type": "call",
            }
            await logger(log_data_before)

            try:
                result = await func(*args, **kwargs)
                formatted_result = repr(result)[:argument_max_length]
                log_data_after = {
                    "message": f"Function returned: {func.__name__} -> {formatted_result}",
                    "function": func.__name__,
                    "result": formatted_result,
                    "log_type": "return",
                }
                await logger(log_data_after)
                return result
            except Exception as e:
                exc_type = type(e)
                exc_val = str(e)
                log_data_exception = {
                    "message": f"Exception in {func.__name__}: {exc_type.__name__} - {exc_val}",
                    "function": func.__name__,
                    "exception_type": exc_type.__name__,
                    "exception": exc_val,
                    "log_type": "exception",
                }
                await logger(log_data_exception)
                raise  # Re-raise the exception

        return wrapper

    return decorator


def async_exception_handling(
    func: Callable[..., Coroutine[Any, Any, None]]
) -> Callable[..., Coroutine[Any, Any, None]]:

    def sync_wrapper(*args: Any, **kwargs: Any) -> Coroutine[Any, Any, Any]:
        async def async_wrapper(*inner_args: Any, **inner_kwargs: Any) -> Any:
            try:
                return await func(*inner_args, **inner_kwargs)
            except Exception as e:
                # In a real scenario, you would likely use a proper logging mechanism
                print(f"Caught exception in {func.__name__}: {e}")
                # Here, we'll simulate logging by returning a dictionary
                return {"tags": ["exception"], "message": str(e)}

        return async_wrapper(*args, **kwargs)

    return sync_wrapper


def async_log_arguments(logger_func: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]):
    """
    An asynchronous decorator to log the arguments of an async function.

    Args:
        logger_func: An async function that accepts a dictionary containing
                     the log information.
    """

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            signature = inspect.signature(func)
            bound_arguments = signature.bind(*args, **kwargs)
            bound_arguments.apply_defaults()
            arguments_log = {name: str(value) for name, value in bound_arguments.arguments.items()}
            log_data = {
                "message": f"Function arguments: {json.dumps({'function': func.__name__, 'args': arguments_log, 'kwargs': kwargs})}",
                "function": func.__name__,
                "args": arguments_log,
                "kwargs": kwargs,
                "log_type": "arguments",
            }
            await logger_func(log_data)
            return await func(*args, **kwargs)

        return wrapper

    return decorator


@dataclass
class AsyncTimer:
    """Time your async code using a class, context manager, or decorator"""

    name: str = field(default_factory=lambda: str(uuid.uuid4()))
    message: str = FINISH
    logger: Union[Logger, Callable[[Dict[str, Any]], Union[None, Coroutine[Any, Any, None]]]] = field(
        default=logger_console
    )
    _start_times: Dict[int, float] = field(default_factory=dict, init=False, repr=False)
    log_arguments: bool = True
    suppress_exceptions: bool = False
    recursive: bool = False
    recurse_depths: Dict[int, float] = field(default_factory=lambda: defaultdict(float))
    argument_max_length: int = 10000

    def __post_init__(self) -> None:
        """Ensure logger is callable."""
        if not callable(self.logger):
            raise ValueError("Logger must be a callable function.")

    def __call__(self, func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            thread_id: int = get_ident()
            function_name = func.__name__

            await self._log_async({"message": START.format(function_name, thread_id)})

            if thread_id in self._start_times and self.recursive:
                self.recurse_depths[thread_id] += 1
                await self._log_async(
                    {"message": f"Recursing in {function_name}, depth = {self.recurse_depths[thread_id]}"}
                )

            self._start_times[thread_id] = start_time

            value: Any
            try:
                value = await func(*args, **kwargs)
            except Exception as exc:
                trace = traceback.format_exc()
                await self._log_async({"message": f"Exception in {function_name}: {trace}", "tags": ["exception"]})
                if not self.suppress_exceptions:
                    elapsed_time = time.perf_counter() - self._start_times.pop(thread_id, time.perf_counter())
                    await self.report(elapsed_time=elapsed_time, func_name=function_name, thread_id=thread_id)
                    raise
                value = f"An exception occurred! {exc}"

            if self.log_arguments:
                arg_reprs = [repr(arg)[:self.argument_max_length] for arg in args]
                kwarg_reprs = {k: repr(v)[:self.argument_max_length] for k, v in kwargs.items()}
                await self._log_async(
                    {
                        "message": f"Function {function_name} executed.",
                        "args": arg_reprs,
                        "kwargs": kwarg_reprs,
                        "result": repr(value)[:self.argument_max_length]
                    }
                )

            elapsed_time = time.perf_counter() - self._start_times.pop(thread_id, time.perf_counter())
            await self.report(elapsed_time=elapsed_time, func_name=function_name, thread_id=thread_id)
            return value

        return wrapper

    async def __aenter__(self) -> "AsyncTimer":
        self._context_start_time = time.perf_counter()
        thread_id: int = get_ident()
        await self._log_async({"message": START.format(self.name, thread_id)})
        return self

    async def __aexit__(
        self, exc_type: Optional[type[BaseException]], exc_val: Optional[BaseException],
        exc_tb: Optional[traceback.TracebackException]
    ) -> None:
        elapsed_time = time.perf_counter() - self._context_start_time
        thread_id: int = get_ident()
        await self.report(elapsed_time=elapsed_time, func_name=self.name, thread_id=thread_id)
        if exc_type and not self.suppress_exceptions:
            raise

    async def start(
        self,
        func: Optional[Callable[..., Any]] = None,
        instance: Optional[Any] = None,
        args: Optional[Any] = None,
        kwargs: Optional[Any] = None
    ) -> None:
        """Start a new timer"""
        thread_id: int = get_ident()
        function_name = self._get_function_name(func)

        await self._log_async({"message": START.format(function_name, thread_id)})

        if thread_id in self._start_times:
            if self.recursive:
                self.recurse_depths[thread_id] += 1
                await self._log_async({"message": f"Recursing, depth = {self.recurse_depths[thread_id]}"})
                return
        else:
            self._start_times[thread_id] = time.perf_counter()

    async def stop(self, func: Optional[Callable[..., Any]] = None) -> float:
        """Stop the timer, and report the elapsed time"""
        thread_id: int = get_ident()

        if self.recurse_depths[thread_id]:
            self.recurse_depths[thread_id] -= 1
            if self.recursive:
                return 0.0

        # Calculate elapsed time
        elapsed_time = time.perf_counter() - self._start_times.pop(thread_id, time.perf_counter())

        # Report elapsed time
        func_name = self._get_function_name(func)
        await self.report(elapsed_time=elapsed_time, func_name=func_name, thread_id=thread_id)

        return elapsed_time

    async def report(
        self,
        elapsed_time: float,
        func_name: Optional[str] = None,
        thread_id: Optional[int] = None,
    ) -> None:
        name: str = func_name or CONTEXT

        message = self.message.format(elapsed_time, name, thread_id)
        log: Dict[str, Any] = {
            "message": message,
            "duration": elapsed_time,
            "tags": ["timing"],
        }
        await self._log_async(log)

    async def _log_async(self, log: Dict[str, Any]) -> None:
        """Helper function to log synchronously or asynchronously"""
        if iscoroutinefunction(self.logger):
            await self.logger(log)  # Async logger
        else:
            self.logger(log)  # type:ignore # Sync logger

    def _get_function_name(self, func: Optional[Callable[..., Any]]) -> str:
        """Helper function to get the function name safely"""
        if func is None:
            return "UNKNOWN_FUNCTION_NAME"
        return getattr(func, '__name__', str(func))
