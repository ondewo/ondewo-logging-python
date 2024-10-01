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

from time import sleep

from ondewo.logging.decorators import Timer
from ondewo.logging.logger import logger_console as log


class MyClass():

    # instance method
    @Timer(logger=log.debug, log_arguments=False, message="MyClass: my_method: Elapsed time: {:0.3f}")
    def my_method(
        self,
        my_variable_str: str,
        my_variable_float: float,
    ) -> None:
        log.debug(f"My debug message {my_variable_str}")
        log.warning(f"My warning message {my_variable_float}")
        log.info("My info message")

        with Timer(message="Timing: Elapsed time: {:0.3f}:", logger=log.debug):
            for i in range(0, 3):
                log.debug("This is my debug message output from within Timer")
                sleep(1)

        try:
            # throw exception
            assert False
        except AssertionError:
            # except exception and log error
            log.error("My error message")

    # classmethod
    @classmethod
    @Timer(
        logger=log.debug, log_arguments=False,
        message="MyClass: my_class_method: Elapsed time: {:0.3f}",
    )
    def my_class_method(
        cls,
        my_variable_str: str,
        my_variable_float: float,
    ) -> None:
        log.debug(f"My debug message {my_variable_str}")
        log.warning(f"My warning message {my_variable_float}")

        with Timer(message="Timing: Elapsed time: {:0.3f}:", logger=log.debug):
            for i in range(0, 3):
                log.debug("This is my debug message output from within Timer")
                sleep(1)

    # staticmethod
    @staticmethod
    @Timer(
        logger=log.debug, log_arguments=True,
        message="MyClass: my_static_method_with_long_method_name: Elapsed time: {:0.3f}",
    )
    def my_static_method_with_long_method_name(
        my_variable_str: str,
        my_variable_float: float,
    ) -> None:
        log.debug(f"My debug message {my_variable_str}")
        log.warning(f"My warning message {my_variable_float}")

        with Timer(message="Timing: Elapsed time: {:0.3f}:", logger=log.debug):
            for i in range(0, 3):
                log.debug("This is my debug message output from within Timer")
                sleep(1)


if __name__ == "__main__":

    # instance method
    my_class: MyClass = MyClass()
    my_class.my_method(
        my_variable_str="my_variable_instance_method_str_hello",
        my_variable_float=1.234,
    )

    # class method
    MyClass.my_class_method(
        my_variable_str="my_variable_classmethod_str_hello",
        my_variable_float=1.234,
    )

    # static method
    MyClass.my_static_method_with_long_method_name(
        my_variable_str="my_variable_str_static_method_hello",
        my_variable_float=5.678,
    )
