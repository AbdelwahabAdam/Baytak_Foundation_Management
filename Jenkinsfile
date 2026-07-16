pipeline {
    agent any

    triggers {
        pollSCM('*/5 * * * *')
    }

    environment {
        DOCKER_USER = 'abdelwahabadam'
        IMAGE_TAG = "${BUILD_NUMBER}"
        DOCKER_CREDENTIALS = credentials('docker-credentials')
    }

    stages {

        stage('Docker Login') {
            steps {
                echo "Logging into Docker Hub..."
                sh '''
                    echo ${DOCKER_CREDENTIALS_PSW} | docker login \
                        -u ${DOCKER_CREDENTIALS_USR} \
                        --password-stdin
                '''
            }
        }

        stage('Build Images') {
            steps {
                sh '''
                    # Backend
                    docker build \
                        -t ${DOCKER_USER}/baytak:backend-${IMAGE_TAG} \
                        -t ${DOCKER_USER}/baytak:backend-latest \
                        ./backend

                    # Frontend
                    docker build \
                        -t ${DOCKER_USER}/baytak:frontend-${IMAGE_TAG} \
                        -t ${DOCKER_USER}/baytak:frontend-latest \
                        ./frontend
                '''
            }
        }

        stage('Verify Images') {
            steps {
                sh 'docker images | grep baytak'
            }
        }

        stage('Push Images') {
            steps {
                sh '''
                    # Backend
                    docker push ${DOCKER_USER}/baytak:backend-${IMAGE_TAG}
                    docker push ${DOCKER_USER}/baytak:backend-latest

                    # Frontend
                    docker push ${DOCKER_USER}/baytak:frontend-${IMAGE_TAG}
                    docker push ${DOCKER_USER}/baytak:frontend-latest
                '''
            }
        }

        stage('Deploy') {
            steps {
                script {
                    sh '''
                        pwd
                        ls -la
                        cat ansible/inventory.ini
                    '''

                    def SERVER_IP = sh(
                        script: """
                            awk '/^\\[baytak\\]/{getline; print \$1}' ansible/inventory.ini
                        """,
                        returnStdout: true
                    ).trim()

                    if (!SERVER_IP) {
                        error "SERVER_IP is empty. Check inventory.ini for [baytak] section"
                    }

                    echo "Deploying to ${SERVER_IP}"

                    sshagent(credentials: ['ec2-key']) {
                        sh """
                            ssh -o StrictHostKeyChecking=no ubuntu@${SERVER_IP} '
                                cd /opt/baytak || exit 1
                                helm upgrade --install baytak ./helm \\
                                    --namespace baytak \\
                                    --set backend.image.tag=backend-${IMAGE_TAG} \\
                                    --set frontend.image.tag=frontend-${IMAGE_TAG}
                            '
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            sh '''
                docker image prune -af || true
                docker builder prune -af || true
                docker logout || true
            '''
        }

        success {
            echo "Docker images built, pushed and deployed successfully."
        }

        failure {
            echo "Pipeline failed."
        }
    }
}