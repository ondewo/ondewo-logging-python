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

from copy import deepcopy
from logging import (
    Filter,
    LogRecord,
)
from threading import get_ident
from typing import (
    Any,
    Dict,
    Optional,
)


class ThreadContextFilter(Filter):
    """This filter adds a dictionary with context info to each log record logged in the current thread."""

    def __init__(
        self, name: str = "", context_dict: Optional[Dict[str, Any]] = None
    ) -> None:
        """

        Args:
            name: filter name (see the superclass for description)
            context_dict: optional dictionary with context information
        """
        super().__init__(name=name)
        self.thread_id: int = get_ident()
        self.context_dict: Dict[str, Any] = context_dict or {}

    def filter(self, record: LogRecord) -> bool:
        """Add the context information to the log record if it comes from the same thread.

        NOTE: message from the log record is first copied and only then updated with the context info

        Args:
            record: log record with log message and thread ID and name

        Returns:
            True if the record should be eventually logged (always)
        """
        if self._is_thread_id_equal(record=record) and isinstance(record.msg, dict):
            record.msg = deepcopy(record.msg)
            record.msg.update(self.context_dict)
        return True

    def _is_thread_id_equal(self, record: LogRecord) -> bool:
        """Check if the record thread is equal to the thread, where this filter was initialized.

        The result is True even when the record thread contains the filter thread ID in its name, e.g.

            self.thread_id = 140248095500096
            str(self.thread_id) in 'my-sub-thread-140248095500096'

        Args:
            record: log record with log message and thread ID and name

        Returns:
            True if the record comes from the same thread as the thread of filter initialization
        """
        return (
            record.thread == self.thread_id or str(self.thread_id) in record.threadName  # type:ignore
        )
