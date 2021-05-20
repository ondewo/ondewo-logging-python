START: str = "Starting {!r} in thread {}."
FINISH: str = "Elapsed time: {:0.4f} seconds. Finished {!r} in thread {}."
CONTEXT: str = "ContextManager"

EXCEPTION: str = "An exception '{}' occurred, with message '{}'. Traceback is in debug log. Finished {!r}."


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""
