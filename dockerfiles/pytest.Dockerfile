FROM python:3.7-slim

WORKDIR /home/ondewo

COPY requirements.txt .
RUN \
      pip3 install -U pip && \
      pip3 install pytest && \
      pip3 install -r requirements.txt

ARG TESTFILE
COPY $TESTFILE $TESTFILE
COPY tests $TESTFILE/tests

CMD python3 -m pytest -vv --capture=no --junit-xml=log/"$RESULTS" "$TESTFILE"
