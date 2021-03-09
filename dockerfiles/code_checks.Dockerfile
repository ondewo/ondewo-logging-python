FROM dockerregistry.ondewo.com:5000/python/python:3.7-slim

RUN \
     apt-get update && apt-get install make && \
     pip install flake8 mypy

RUN mkdir code_to_test
WORKDIR code_to_test

ARG FOLDER_NAME
COPY $FOLDER_NAME $FOLDER_NAME
COPY dockerfiles/code_checks .
