PACKAGE_FOLDER := ondewo-logging-python
TESTFILE := ondewo
CODE_CHECK_IMAGE := code_check_image_${TESTFILE}
IMAGE_NAME := dockerregistry.ondewo.com:5000/ondewo-
FLUENTD_PATH := ondewo-logging/fluentd

all: setup_folders

setup_folders:
	git submodule update --init
	mkdir ${FLUENTD_PATH}/log -p
	sudo chown -R 100:$$(id -u) ${FLUENTD_PATH}/log

run_code_checks: ## Start the code checks image and run the checks
	docker build -t ${CODE_CHECK_IMAGE} --build-arg FOLDER_NAME=${TESTFILE} -f dockerfiles/code_checks.Dockerfile .
	docker run --rm ${CODE_CHECK_IMAGE} make flake8
	docker run --rm -e FOLDER_NAME=${TESTFILE} ${CODE_CHECK_IMAGE} make mypy

run_tests: ## Start a server then a little docker image to run the e2e tests in
	docker build -t pytest_image --build-arg TESTFILE=${TESTFILE} -f dockerfiles/pytest.Dockerfile .
	docker run --rm --network host -e RESULTS=x -e TESTFILE=${TESTFILE} pytest_image

push_to_pypi: build_package upload_package clear_package_data
	echo pushed to pypi : \)

build_package:
	python setup.py sdist bdist_wheel

upload_package:
	twine upload -r pypi dist/*

clear_package_data:
	rm -rf build dist ondewo_logging.egg-info
