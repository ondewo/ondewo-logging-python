pipeline {
    agent any
    environment{
        PROJECT_FOLDER = "ondewologging"
        component = "ondewo-logging"

        branch_name = "${env.BRANCH_NAME.replace("/", "_")}"
        _version = "${(branch_name.startsWith("release_")) ? "staging" : "${branch_name}"}"
        delivery_policy = "${branch_name.startsWith("master") ? "production" \
            : (branch_name.startsWith("release") ? "staging" \
            : (branch_name.startsWith("develop") ? "develop" \
            : "branch")) \
        }"
        git_version_tag = "${sh(returnStdout: true, script: "git tag --sort version:refname | grep -E '^[[:digit:]]+\\.[[:digit:]]+\\.[[:digit:]]+\$' | tail -1").trim()}"
        // if we are on master, get the latest commit tag
        image_suffix = "${delivery_policy.startsWith("production") ? git_version_tag \
        : (delivery_policy.startsWith("staging") ? "${git_version_tag}-rc${env.BUILD_ID}" \
        : (delivery_policy.startsWith("develop") ? "develop" \
        : branch_name))}"
        PUSH_NAME = "dockerregistry.ondewo.com:5000/${component}:${image_suffix}"
        RELEASE_NAME = "dockerregistry.ondewo.com:5000/${component}-release:${image_suffix}"
        RELEASE_NAME_LATEST = "dockerregistry.ondewo.com:5000/${component}-release:latest"
        release_base_folder = "/home/jenkins/releases"
        release_folder = "${release_base_folder}/${component}/${image_suffix}"
        release_file = "${release_folder}/${component}-release-${image_suffix}.tar"

        TEST_IMAGE_NAME = "test_image_${component}"
        CODE_CHECK_IMAGE_NAME = "code_check_image_${component}"
    }

    stages {
        stage('Code quality') { agent { label 'cpu' }
            steps {
                sh(script: "make run_code_checks")
        } }

        stage('Test') {
            environment {
                testresults_folder = pwd()
                testresults_filename = "pytest_unit.xml"
            }
            steps {
                sh(script: "docker build -t ${TEST_IMAGE_NAME} --build-arg TESTFILE=${PROJECT_FOLDER} -f dockerfiles/pytest.Dockerfile .", label: "build test image")
                sh(script: "docker run --rm -v ${testresults_folder}:/tmp/transfer/log -e RESULTS=${testresults_filename} -e TESTFILE=${PROJECT_FOLDER} ${TEST_IMAGE_NAME}", label: "start the test image and run the tests")
            }
            post { always {
                junit "${testresults_filename}"
            } }
        }

        stage('Package Image') {
            agent { label 'cpu' }
            when { expression {
                    delivery_policy.startsWith("production")
            } }
            steps {
                sh "echo \"Releasing ${component} - ${env.BRANCH_NAME}\""
                sh 'printenv'
                sh(script: "make -f package.Makefile build_package", label: "build package")
        } }
} }
