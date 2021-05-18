from logging import Filter, LogRecord
from threading import get_ident
from typing import Any, Dict


class ContextFilter(Filter):
    def __init__(self, context_dict: Dict[str, Any]) -> None:
        self.thread_id: int = get_ident()
        self.context_dict: Dict[str, Any] = context_dict

    def filter(self, record: LogRecord) -> bool:
        if self._is_thread_id_equal(record=record) and isinstance(record.msg, dict):
            record.msg.update(self.context_dict)
        return True

    def _is_thread_id_equal(self, record: LogRecord) -> bool:
        return record.thread == self.thread_id or record.threadName.endswith(
            str(self.thread_id)
        )
