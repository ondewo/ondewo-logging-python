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

FROM python:3.12-slim

RUN \
     apt-get update \
     && apt-get install make \
     && apt autoremove \
     && apt clean \
     && pip install flake8 mypy

RUN mkdir code_to_test
WORKDIR code_to_test

ARG FOLDER_NAME
COPY $FOLDER_NAME $FOLDER_NAME
COPY dockerfiles/code_checks .

# install mypy types
COPY requirements-static-code-checks.txt .
RUN pip install -r requirements-static-code-checks.txt
