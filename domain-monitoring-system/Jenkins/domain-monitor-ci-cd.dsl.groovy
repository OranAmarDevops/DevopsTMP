// Reference pipeline: build, smoke-test and optionally publish the application.
def commitId

pipeline {
    agent { label 'docker' }

    parameters {
        booleanParam(name: 'PUSH_TO_DOCKER_HUB', defaultValue: false, description: 'Push the tested image to Docker Hub')
    }

    environment {
        IMAGE_REPOSITORY = 'oranamar2003/domain-monitoring-system'
        DOCKER_CREDENTIALS_ID = 'docker'
        TEST_CONTAINER = 'domain-monitor-test'
    }

    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                checkout scm
                script {
                    commitId = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.BUILD_IMAGE = "${env.IMAGE_REPOSITORY}:${commitId}"
                }
            }
        }

        stage('Build') {
            steps {
                sh 'sudo docker build -t "$BUILD_IMAGE" .'
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    sudo docker rm -f "$TEST_CONTAINER" 2>/dev/null || true
                    sudo docker run -d --name "$TEST_CONTAINER" "$BUILD_IMAGE"
                    sleep 5
                    sudo docker exec "$TEST_CONTAINER" python -c "import json, urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:5000/health')); assert data['status'] == 'healthy'"
                '''
            }
        }

        stage('Push') {
            when { expression { params.PUSH_TO_DOCKER_HUB } }
            steps {
                withCredentials([usernamePassword(credentialsId: env.DOCKER_CREDENTIALS_ID, usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "$DOCKER_PASS" | sudo docker login -u "$DOCKER_USER" --password-stdin
                        sudo docker push "$BUILD_IMAGE"
                        sudo docker tag "$BUILD_IMAGE" "${IMAGE_REPOSITORY}:latest"
                        sudo docker push "${IMAGE_REPOSITORY}:latest"
                        sudo docker logout
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'sudo docker rm -f "$TEST_CONTAINER" 2>/dev/null || true'
        }
    }
}
