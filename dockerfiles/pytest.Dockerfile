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

WORKDIR /home/ondewo

COPY requirements.txt .
RUN \
      pip3 install -U pip && \
      pip3 install pytest && \
      pip3 install -r requirements.txt

ARG TESTFILE
COPY $TESTFILE $TESTFILE
COPY tests tests

CMD python3 -m pytest -vv --capture=no --junit-xml=log/"$RESULTS" "tests"
