pipeline {
  agent {
     node { 
        label 'CentOS8'
        } 
  }
  stages {
    stage('Checkout Scm') {
      steps {
        git 'eolJenkins:NCAR/MTP.git'
      }
    }
    wrap([$class: 'Xvfb', additionalOptions: '', assignedLabels: '', autoDisplayName: true, debug: true, displayNameOffset: 0, installationName: 'XVFB', parallelBuild: true, screen: '1024x758x24', timeout: 25]) {
      stage('Shell script 0') {
        steps {
          sh '''cd tests
# This build depends on EOL-Python. Not sure if this is the *best* way to
# do this, but it works, so for now...
export PYTHONPATH=\'/var/lib/jenkins/workspace/EOL-Python/src\'
export PATH=/opt/local/anaconda3/bin:/opt/local/anaconda3/pkgs:$PATH
eval "$(conda shell.bash hook)"
# Only create if /var/lib/jenkins/.conda/envs/mtp doesn\'t exist. Add a check
# conda env create -f ../mtpenv.yml
conda activate mtp
./run_tests.sh'''
        }
      }
    }
  }
  post {
    always {
      mail(body: 'The body', to: 'janine@ucar.edu')
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
