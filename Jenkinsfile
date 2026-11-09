// Declarative Pipeline: the whole CI/CD process written as code.
pipeline {
    agent any                                  // run on any available Jenkins machine

    options {
        timestamps()                           // show time on every log line
        timeout(time: 15, unit: 'MINUTES')     // never let a build hang forever
        buildDiscarder(logRotator(numToKeepStr: '10'))  // keep only last 10 builds
    }

    environment {
        IMAGE_NAME     = 'jenkins-demo-app'
        CONTAINER_NAME = 'jenkins-demo-app'
        NETWORK        = 'cicd-net'            // same Docker network Jenkins is on
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm                   // pull the code from Git
            }
        }

        stage('Test') {
            steps {
                // Builds only the "test" stage of the Dockerfile; runs pytest inside it.
                sh 'docker build --target test -t ${IMAGE_NAME}:test .'
            }
        }

        stage('Build Image') {
            steps {
                sh '''
                  docker build \
                    --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                    -t ${IMAGE_NAME}:${BUILD_NUMBER} \
                    -t ${IMAGE_NAME}:latest .
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                  docker rm -f ${CONTAINER_NAME} || true
                  docker run -d \
                    --name ${CONTAINER_NAME} \
                    --network ${NETWORK} \
                    -p 5000:5000 \
                    --restart unless-stopped \
                    ${IMAGE_NAME}:${BUILD_NUMBER}
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                // Try up to 10 times: is the new container really answering?
                sh '''
                  for i in 1 2 3 4 5 6 7 8 9 10; do
                    if curl -fs http://${CONTAINER_NAME}:5000/health; then
                      echo " <- app is healthy"
                      exit 0
                    fi
                    echo "waiting for app... ($i)"
                    sleep 3
                  done
                  echo "App did not become healthy"
                  exit 1
                '''
            }
        }
    }

    post {
        success { echo "SUCCESS: open http://localhost:5000 to see build #${env.BUILD_NUMBER}" }
        failure {
            echo 'FAILED: check the stage that turned red in the console log'
            sh 'docker logs ${CONTAINER_NAME} || true'
        }
        always {
            sh 'docker image prune -f || true'   // clean unused images
        }
    }
}
