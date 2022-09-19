*****************
# Release History
*****************

## Release ONDEWO LOGGING PYTHON 3.2.6

### Bug Fixes

* Bug fix function name

*****************

## Release ONDEWO LOGGING PYTHON 3.2.5

### Bug Fixes

* logging.yaml was not included in the build, because MANIFEST.in was not
  included in the Dockerfile.utils

*****************

## Release ONDEWO LOGGING PYTHON 3.2.4

### Bug Fixes

* logging.yaml was not included in the build

*****************

## Release ONDEWO LOGGING PYTHON 3.2.3

### Bug Fixes

* logging.yaml was not included in the build

*****************

## Release ONDEWO LOGGING PYTHON 3.2.2

### Bug Fixes

* Added setuptools>=59.5.0 to requirements

*****************

## Release ONDEWO LOGGING PYTHON 3.2.1

### Bug Fixes

* Makefile and release automation

*****************

## Release ONDEWO LOGGING PYTHON 3.2.0

### Improvements

* Release Automation

*****************

## Release ONDEWO LOGGING PYTHON 3.1.0

### Breaking Changes

* Make logging read yaml from another location (/home/ondewo/logging.yaml)

### Improvements

* Update fluent-logger to 0.10.0
* Change console logger to use debug handler by default

### Bug Fixes

* Reformat some files
* Update readme

*****************

## Release ONDEWO LOGGING PYTHON 3.0.0

### Breaking Changes

* Remove fluentd

*****************

## Release ONDEWO LOGGING PYTHON 2.0.3

### New Features

* [OND233-212] enable decorators to be used in concurrent function execution
* [OND233-212] add thread context logger, which attaches thread-specific context information to all the logs

### Bug Fixes

* [OND233-212] fix duration in Timer decorator

*****************

## Release ONDEWO LOGGING PYTHON 2.0.2

### Bug Fixes

* fix error logging bug related to exc.args iterable

*****************

## Release ONDEWO LOGGING PYTHON 2.0.1

### Bug Fixes

* Little spelling errors and other things in README etc.

*****************

## Release ONDEWO LOGGING PYTHON 2.0.0

### New Features

* now in the pypi!

### Breaking Changes

* no longer available under 'ondewologging', now 'ondewo.logging'

### Migration Guide

* pip install "ondewo-logging==2.0.0"

*****************

## Release ONDEWO LOGGING PYTHON 1.6.1

### Bug Fixes

* fixed bug in exception_handling decorator

*****************

## Release ONDEWO LOGGING PYTHON 1.6.0

### New Features

* Deleted Jenkinsfile
* Fixed LICENSE

### Known issues not covered in this release

No replacement for build pipelines yet, will get to this after we learn a little about gihub pipelines.


*****************

## Release ONDEWO LOGGING PYTHON 1.5.1

### New Features

* Looks in the repository root for a logging.yaml.
* Complains if you don't have the required env vars (git repo, docker image etc.)

### Improvements

Easier to import logging config.


*****************

## Release ONDEWO LOGGING PYTHON 1.5.0

### New Features

Better support for GRPC messages including serialization and optional truncation.

### Improvements

Improved README and LICENCE

### Breaking Changes

Moving to Github! So old installs wont work anymore.

### Migration Guide

[Replace submodule](https://stackoverflow.com/a/1260982/7756727) in the client.

*****************

# RELEASE TEMPLATE

### New Features

### Improvements

### Bug fixes

### Breaking Changes

### Known issues not covered in this release

### Migration Guide
