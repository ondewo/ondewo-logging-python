PACKAGE_FOLDER := ondewo-logging-python
TESTFILE := ondewo
CODE_CHECK_IMAGE := code_check_image_${TESTFILE}

run_code_checks: ## Start the code checks image and run the checks
	docker build -t ${CODE_CHECK_IMAGE} --build-arg FOLDER_NAME=${TESTFILE} -f dockerfiles/code_checks.Dockerfile .
	docker run --rm ${CODE_CHECK_IMAGE} make flake8
	docker run --rm -e FOLDER_NAME=${TESTFILE} ${CODE_CHECK_IMAGE} make mypy

run_tests: ## Start a server then a little docker image to run the e2e tests in
	docker build -t pytest_image --build-arg TESTFILE=${TESTFILE} -f dockerfiles/pytest.Dockerfile .
	docker run --rm --network host -e RESULTS=x -e TESTFILE=${TESTFILE} pytest_image

export

# PR BEFORE RELEASE
# 1 - Update Version Number
# 2 - Update RELEASE.md
# 3 - make update_setup
#
# Fully automated build and deploy process for ondewo-logging-client-python
# Release Process Steps:
# 1 - Create Release Branch and push
# 2 - Create Release Tag and push
# 3 - GitHub Release
# 4 - PyPI Release

# MUST BE THE SAME AS API in Mayor and Minor Version Number
# example: API 2.9.0 --> Client 2.9.X
ONDEWO_LOGGING_VERSION=3.3.3


PYPI_USERNAME?=ENTER_HERE_YOUR_PYPI_USERNAME
PYPI_PASSWORD?=ENTER_HERE_YOUR_PYPI_PASSWORD

# You need to setup an access token at https://github.com/settings/tokens - permissions are important
GITHUB_GH_TOKEN?=ENTER_YOUR_TOKEN_HERE

CURRENT_RELEASE_NOTES=`cat RELEASE.md \
	| sed -n '/Release ONDEWO LOGGING PYTHON ${ONDEWO_LOGGING_VERSION}/,/\*\*/p'`


# Choose repo to release to - Example: "https://github.com/ondewo/ondewo-nlu-client-python"
GH_REPO="https://github.com/ondewo/ondewo-logging-python"

# Submodule paths

# Specify protos directories

# Utils release docker image environment variables
IMAGE_UTILS_NAME=ondewo-logging-utils-python:${ONDEWO_LOGGING_VERSION}

.DEFAULT_GOAL := help

########################################################
#       ONDEWO Standard Make Targets
########################################################

setup_developer_environment_locally: install_precommit_hooks install_dependencies_locally

install_precommit_hooks: ## Installs pre-commit hooks and sets them up for the ondewo-csi-client repo
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type commit-msg

precommit_hooks_run_all_files: ## Runs all pre-commit hooks on all files and not just the changed ones
	pre-commit run --all-file

install_dependencies_locally: ## Install dependencies locally
	pip install -r requirements-dev.txt
	pip install -r requirements.txt

flake8: ## Runs flake8
	flake8 .

mypy: ## Run mypy static code checking
	pre-commit run mypy --all-files

help: ## Print usage info about help targets
	# (first comment after target starting with double hashes ##)
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

makefile_chapters: ## Shows all sections of Makefile
	@echo `cat Makefile| grep "########################################################" -A 1 | grep -v "########################################################"`

# BEFORE "release"
update_setup: ## Update Logging Version in setup.py
	@sed -i "s/version='[0-9]*.[0-9]*.[0-9]*'/version='${ONDEWO_LOGGING_VERSION}'/g" setup.py

release: create_release_branch create_release_tag build_and_release_to_github_via_docker build_and_push_to_pypi_via_docker ## Automate the entire release process
	@echo "Release Finished"

create_release_branch: ## Create Release Branch and push it to origin
	git checkout -b "release/${ONDEWO_LOGGING_VERSION}"
	git push -u origin "release/${ONDEWO_LOGGING_VERSION}"

create_release_tag: ## Create Release Tag and push it to origin
	git tag -a ${ONDEWO_LOGGING_VERSION} -m "release/${ONDEWO_LOGGING_VERSION}"
	git push origin ${ONDEWO_LOGGING_VERSION}

build_and_push_to_pypi_via_docker: push_to_pypi_via_docker_image  ## Release automation for building and pushing to pypi via a docker image

build_and_release_to_github_via_docker: build_utils_docker_image release_to_github_via_docker_image  ## Release automation for building and releasing on GitHub via a docker image

login_to_gh: ## Login to Github CLI with Access Token
	echo $(GITHUB_GH_TOKEN) | gh auth login -p ssh --with-token

build_gh_release: ## Generate Github Release with CLI
	gh release create --repo $(GH_REPO) "$(ONDEWO_LOGGING_VERSION)" -n "$(CURRENT_RELEASE_NOTES)" -t "Release ${ONDEWO_LOGGING_VERSION}"

install:  ## Install requirements
	pip install .
	pip install -r requirements.txt

build_utils_docker_image:  ## Build utils docker image
	docker build -f Dockerfile.utils -t ${IMAGE_UTILS_NAME} .

push_to_pypi_via_docker_image:  ## Push source code to pypi via docker
	[ -d $(OUTPUT_DIR) ] || mkdir -p $(OUTPUT_DIR)
	docker run --rm \
		-v ${shell pwd}/dist:/home/ondewo/dist \
		-e PYPI_USERNAME=${PYPI_USERNAME} \
		-e PYPI_PASSWORD=${PYPI_PASSWORD} \
		${IMAGE_UTILS_NAME} make push_to_pypi
	rm -rf dist

show_pypi: build_package
	tar xvfz dist/ondewo-logging-${ONDEWO_LOGGING_VERSION}.tar.gz
	tree ondewo-logging-${ONDEWO_LOGGING_VERSION}

show_pypi_via_docker_image: build_utils_docker_image ## Push source code to pypi via docker
	[ -d $(OUTPUT_DIR) ] || mkdir -p $(OUTPUT_DIR)
	docker run --rm \
		-v ${shell pwd}/dist:/home/ondewo/dist \
		-e PYPI_USERNAME=${PYPI_USERNAME} \
		-e PYPI_PASSWORD=${PYPI_PASSWORD} \
		${IMAGE_UTILS_NAME} make show_pypi
	rm -rf dist


push_to_pypi: build_package upload_package clear_package_data
	@echo 'YAY - Pushed to pypi : )'

push_to_gh: login_to_gh build_gh_release
	@echo 'Released to Github'

release_to_github_via_docker_image:  ## Release to Github via docker
	docker run --rm \
		-e GITHUB_GH_TOKEN=${GITHUB_GH_TOKEN} \
		${IMAGE_UTILS_NAME} make push_to_gh

build_package:
	python setup.py sdist bdist_wheel
	chmod a+rw dist -R

upload_package:
	twine upload --verbose -r pypi dist/* -u${PYPI_USERNAME} -p${PYPI_PASSWORD}

clear_package_data:
	rm -rf build dist/* ondewo_logging.egg-info

ondewo_release: spc clone_devops_accounts run_release_with_devops ## Release with credentials from devops-accounts repo
	@rm -rf ${DEVOPS_ACCOUNT_GIT}

clone_devops_accounts: ## Clones devops-accounts repo
	if [ -d $(DEVOPS_ACCOUNT_GIT) ]; then rm -Rf $(DEVOPS_ACCOUNT_GIT); fi
	git clone git@bitbucket.org:ondewo/${DEVOPS_ACCOUNT_GIT}.git

DEVOPS_ACCOUNT_GIT="ondewo-devops-accounts"
DEVOPS_ACCOUNT_DIR="./${DEVOPS_ACCOUNT_GIT}"

TEST:
	@echo ${GITHUB_GH_TOKEN}
	@echo ${PYPI_USERNAME}
	@echo ${PYPI_PASSWORD}
	@echo ${CURRENT_RELEASE_NOTES}

run_release_with_devops:
	$(eval info:= $(shell cat ${DEVOPS_ACCOUNT_DIR}/account_github.env | grep GITHUB_GH & cat ${DEVOPS_ACCOUNT_DIR}/account_pypi.env | grep PYPI_USERNAME & cat ${DEVOPS_ACCOUNT_DIR}/account_pypi.env | grep PYPI_PASSWORD))
	make release $(info)

spc: ## Checks if the Release Branch, Tag and Pypi version already exist
	$(eval filtered_branches:= $(shell git branch --all | grep "release/${ONDEWO_LOGGING_VERSION}"))
	$(eval filtered_tags:= $(shell git tag --list | grep "${ONDEWO_LOGGING_VERSION}"))
	$(eval setuppy_version:= $(shell cat setup.py | grep "version"))
	@if test "$(filtered_branches)" != ""; then echo "-- Test 1: Branch exists!!" & exit 1; else echo "-- Test 1: Branch is fine";fi
	@if test "$(filtered_tags)" != ""; then echo "-- Test 2: Tag exists!!" & exit 1; else echo "-- Test 2: Tag is fine";fi
	@if test "$(setuppy_version)" != "version='${ONDEWO_LOGGING_VERSION}',"; then echo "-- Test 3: Setup.py not updated!!" & exit 1; else echo "-- Test 3: Setup.py is fine";fi
