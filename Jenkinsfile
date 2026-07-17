pipeline {
    agent any

    triggers {
        pollSCM('*/5 * * * *')
    }

    environment {
        DOCKER_USER = 'abdelwahabadam'
        IMAGE_TAG = "${BUILD_NUMBER}"
        DOCKER_CREDENTIALS = credentials('docker-credentials')
        DOCKER_BUILDKIT = "1"

    }

    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                checkout scm
            }
        }
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
            parallel {
                stage('Build Backend') {
                    steps {
                        sh '''
                            docker build \
                                -t ${DOCKER_USER}/baytak:backend-${IMAGE_TAG} \
                                -t ${DOCKER_USER}/baytak:backend-latest \
                                ./backend
                        '''
                    }
                }

                stage('Build Frontend') {
                    steps {
                        sh '''
                            docker build \
                                -t ${DOCKER_USER}/baytak:frontend-${IMAGE_TAG} \
                                -t ${DOCKER_USER}/baytak:frontend-latest \
                                ./frontend
                        '''
                    }
                }
            }
        }

        stage('Verify Images') {
            steps {
                sh 'docker images | grep baytak'
            }
        }

        stage('Push Images') {
            parallel {
                stage('Push Backend') {
                    steps {
                        sh '''
                            docker push ${DOCKER_USER}/baytak:backend-${IMAGE_TAG}
                            docker push ${DOCKER_USER}/baytak:backend-latest
                        '''
                    }
                }

                stage('Push Frontend') {
                    steps {
                        sh '''
                            docker push ${DOCKER_USER}/baytak:frontend-${IMAGE_TAG}
                            docker push ${DOCKER_USER}/baytak:frontend-latest
                        '''
                    }
                }
            }
        }

        stage('Deploy') {
                steps {
                    dir('/home/hopa/baytak/Baytak_Foundation_Management') {
                        sh 'whoami'

                        withCredentials([string(credentialsId: 'ansible-vault-password', variable: 'VAULT_PASSWORD')]) {

                            sshagent(credentials: ['ec2-key']) {

                                sh '''
                                    whoami
                                    echo "$VAULT_PASSWORD" > .vault_pass
                                    chmod 600 .vault_pass
                                    trap "rm -f .vault_pass" EXIT

                                    export ANSIBLE_CONFIG=ansible/ansible.cfg
                                    ansible-playbook ansible/upgrade-helm.yaml \
                                        -i ansible/inventory.ini \
                                        --vault-password-file .vault_pass \
                                        -e backend_tag=backend-${IMAGE_TAG} \
                                        -e frontend_tag=frontend-${IMAGE_TAG}
                                '''
                            }
                        }
                    }
                }
            }
    }

    post {
        always {
            sh '''
                docker image prune -f || true
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