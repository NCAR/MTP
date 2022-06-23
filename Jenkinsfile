pipeline {
  agent {
     node { 
        label 'CentOS8'
        } 
  }
  environment {
    condaenv = fileExists '/var/lib/jenkins/.conda/envs/mtp'
  }
  stages {
    stage('Checkout Scm') {
      steps {
        git 'eolJenkins:NCAR/MTP.git'
      }
    }
    stage('Create Conda env') {
      when { expression { condaenv == 'false' }}
      steps {
        sh ''' # Only create if condaenv dir doesn\'t exist
        /opt/local/anaconda3/bin/conda env create -f ../mtpenv.yml '''
      }
    }
    stage('Shell script 0') {
      steps {
        wrap([$class: 'Xvfb', additionalOptions: '', assignedLabels: '', autoDisplayName: true, debug: true, displayNameOffset: 0, installationName: 'default', parallelBuild: true, screen: '1024x758x24', timeout: '25']) {
          sh '''cd tests
# This build depends on EOL-Python. Not sure if this is the *best* way to
# do this, but it works, so for now...
export PYTHONPATH=\'/var/lib/jenkins/workspace/EOL-Python/src\'
export PATH=/opt/local/anaconda3/bin:/opt/local/anaconda3/pkgs:$PATH
eval "$(conda shell.bash hook)"
conda activate mtp
./run_tests.sh'''
        }
      }
    }
  }
  post {
    failure {
      mail(subject: 'MTP Jenkinsfile build failed', body: 'See build console output within jenkins for details', to: 'janine@ucar.edu cdewerd@ucar.edu cjw@ucar.edu taylort@ucar.edu')
    }

  }
  options {
    buildDiscarder(logRotator(numToKeepStr: '6'))
  }
  triggers {
    upstream(upstreamProjects: 'EOL-Python', threshold: hudson.model.Result.SUCCESS)
    pollSCM('H/5 * * * *')
  }
}
