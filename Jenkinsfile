pipeline {

    agent {
        label 'slave'
    }

    environment {

        IMAGE_NAME = 'flask-app'
        CONTAINER_NAME = 'webapp-flask'
    }

    stages {

        stage('Checkout') {

            steps {

                echo "------ Git Checkout ------"
                git branch: 'main',
                url: 'https://github.com/harikrishnan-knr/Bot-Generated_Ad_Clicks_Identify.git'
                echo "------ Git Checkout Completed ------"
            }
        }

        
  	    stage('Build Docker Image') {

            steps {

                echo "------ Docker Image Build ------"
                sh 'docker build -t ${IMAGE_NAME}:latest .'
                echo "------ Docker Image Build Completed ------"
            }
         }

        stage('Stop Old Container') {

            steps {

                sh 'docker stop ${CONTAINER_NAME} || true'
                sh 'docker rm ${CONTAINER_NAME} || true'
                echo "------ Old Container Stopped ------"
            }
        }
        
        stage('Run Docker Container') {

            steps {

                sh 'docker run -d --name ${CONTAINER_NAME} -p 8090:8080 ${IMAGE_NAME}:latest'
                echo "------ Running Docker Container ------"
            }
        }

        stage('Verify Container') {

            steps {
            
                sh 'docker ps'
                echo "------ Container Process Running ------"
            }
        }
       
    }

post {
        success {
            mail to: 'harikrishnanknr07@gmail.com',
                 subject: "SUCCESS: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                 body: "Build succeeded: ${env.BUILD_URL}"
        }

        failure {
            mail to: 'harikrishnanknr07@gmail.com',
                 subject: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                 body: "Build failed: ${env.BUILD_URL}"
        }
    }
}
