PACKAGE_FOLDER := ondewo-logging-python
TESTFILE := ondewologging
CODE_CHECK_IMAGE := code_check_image_${TESTFILE}
IMAGE_NAME := dockerregistry.ondewo.com:5000/ondewo-

all: setup_folders

setup_folders:
	mkdir fluentd/log -p
	sudo chown -R 100:$$(id -u) fluentd/log

run_code_checks: ## Start the code checks image and run the checks
	docker build -t ${CODE_CHECK_IMAGE} --build-arg FOLDER_NAME=${TESTFILE} -f dockerfiles/code_checks.Dockerfile .
	docker run --rm ${CODE_CHECK_IMAGE} make flake8
	docker run --rm -e FOLDER_NAME=${TESTFILE} ${CODE_CHECK_IMAGE} make mypy

run_tests: ## Start a server then a little docker image to run the e2e tests in
	docker build -t pytest_image --build-arg TESTFILE=${TESTFILE} -f dockerfiles/pytest.Dockerfile .
	docker run --rm --network host -e RESULTS=x -e TESTFILE=${TESTFILE} pytest_image
