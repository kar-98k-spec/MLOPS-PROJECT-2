pipeline {
    agent any

    stages{
        stage("cloning from Github..."){
            steps{
                script{
                    echo' Cloning the repository from GitHub...'
                    checkout scmGit(branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[credentialsId: 'github-token', url: 'https://github.com/kar-98k-spec/MLOPS-PROJECT-2.git']])

                }
            }
        }
    }
}