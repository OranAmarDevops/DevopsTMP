// Reference deployment pipeline: deploy either Docker Hub latest or a fresh local build.
pipeline {
    agent { label 'docker' }

    options {
        timeout(time: 20, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    parameters {
        choice(name: 'IMAGE_SOURCE', choices: ['DOCKER_HUB', 'LOCAL_BUILD'], description: 'Pull latest or build from this commit')
        string(name: 'HOST_PORT', defaultValue: '5000', description: 'Host port exposed by Docker')
    }

    environment {
        IMAGE_REPOSITORY = 'oranamar2003/domain-monitoring-system'
        DEPLOY_IMAGE = 'oranamar2003/domain-monitoring-system:latest'
        CONTAINER_NAME = 'domain-monitor-app'
    }

    stages {
        stage('Checkout') {
            when { expression { params.IMAGE_SOURCE == 'LOCAL_BUILD' } }
            steps {
                cleanWs()
                checkout scm
            }
        }

        stage('Prepare Image') {
            steps {
                script {
                    if (params.IMAGE_SOURCE == 'LOCAL_BUILD') {
                        env.DEPLOY_IMAGE = "${env.IMAGE_REPOSITORY}:local-${env.BUILD_NUMBER}"
                        sh 'sudo docker build -t "$DEPLOY_IMAGE" .'
                    } else {
                        sh 'sudo docker pull "$DEPLOY_IMAGE"'
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    sudo docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
                    sudo docker run -d \
                        --name "$CONTAINER_NAME" \
                        --restart unless-stopped \
                        -p "${HOST_PORT}:5000" \
                        "$DEPLOY_IMAGE"
                    sleep 5
                    sudo docker exec "$CONTAINER_NAME" python -c "import json, urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:5000/health')); assert data['status'] == 'healthy'"
                '''
            }
        }
    }

    post {
        failure {
            sh 'sudo docker logs "$CONTAINER_NAME" 2>/dev/null || true'
        }
    }
}
