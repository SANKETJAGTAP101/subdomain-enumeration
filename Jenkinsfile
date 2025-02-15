pipeline {
    agent any
    environment {
        DOCKER_IMAGE_NAME = "om1201/myapp" // Replace with your Docker Hub username and image name
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/OmBhargude/Ditiss-AUG24.git' // Or specify a branch like '*/main'
            }
        }
        stage('Build and Push Docker Image') {
            steps {
                script {
                    sh "docker build -t ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER} ."

                    withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
                        sh "docker login -u ${USERNAME} -p ${PASSWORD}"
                        sh "docker push ${DOCKER_IMAGE_NAME}:${BUILD_NUMBER}"
                    }
                }
            }
        }
        stage('Deploy to Kubernetes') {
            steps {
        withKubeConfig(credentialsId: 'kubernetes-credentials'){
                        // Deployment doesn't exist, create it along with the service
                        sh "kubectl apply -f deployment.yaml"
                        sh "kubectl apply -f service.yaml"
                    }
                }
            }
        }
}
