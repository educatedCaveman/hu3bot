pipeline {
    agent any 

    environment {
        ANSIBLE_REPO = '/var/lib/jenkins/workspace/ansible_master'
        WEBHOOK = credentials('JENKINS_DISCORD')
        PORTAINER_DEV_WEBHOOK = credentials('PORTAINER_WEBHOOK_DEV_HU3BOT')
        PORTAINER_PRD_WEBHOOK = credentials('PORTAINER_WEBHOOK_PRD_HU3BOT')
        DOCKER_CREDENTIALS = credentials('DOCKER_HUB_CREDENTIALS')
    }

    //triggering periodically so the code is always present
    // run every friday at 3AM
    triggers { cron('0 3 * * 5') }

    node {
        def app

        // ensure we have the code
        stage('Clone repository') {
            checkout scm
        }

        // build the image, using a different name for dev/master
        stage('Build DEV image') {
            when { branch 'dev_test' }
            app = docker.build("drak3/hu3bot-dev")
        }
        stage('Build PRD image') {
            when { branch 'master' }
            app = docker.build("drak3/hu3bot")
        }

        // stage('Test image') {
        //     /* Ideally, we would run a test framework against our image.
        //     * For this example, we're using a Volkswagen-type approach ;-) */

        //     app.inside {
        //         sh 'echo "Tests passed"'
        //     }
        // }

        stage('Push image') {
            /* Finally, we'll push the image with two tags:
            * First, the incremental build number from Jenkins
            * Second, the 'latest' tag.
            * Pushing multiple tags is cheap, as all the layers are reused. */
            docker.withRegistry('https://registry.hub.docker.com', DOCKER_CREDENTIALS) {
                app.push("${env.BUILD_NUMBER}")
                app.push("latest")
            }
        }
        // // deploy code to lv-426.lab, when the branch is 'dev_test'
        // stage('deploy dev code') {
        //     when { branch 'dev_test' }
        //     steps {
        //         // deploy configs to DEV
        //         echo 'deploy docker config files (DEV)'
        //         sh 'ansible-playbook ${ANSIBLE_REPO}/deploy/docker/deploy_docker_compose_dev.yml --extra-vars repo="homer"'
        //     }
        // }
        // // trigger portainer redeploy
        // // separated out so this only gets run if the ansible playbook doesn't fail
        // stage('redeploy portainer stack (DEV)') {
        //     when { branch 'dev_test' }
        //     steps {
        //         // deploy configs to DEV
        //         echo 'Redeploy DEV stack'
        //         sh 'http post ${PORTAINER_DEV_WEBHOOK}'
        //     }
        // }

        // // deploy code to sevastopol, when the branch is 'master'
        // stage('deploy prd code') {
        //     when { branch 'master' }
        //     steps {
        //         // deploy configs to PRD
        //         echo 'deploy docker config files (PRD)'
        //         sh 'ansible-playbook ${ANSIBLE_REPO}/deploy/docker/deploy_docker_compose_prd.yml --extra-vars repo="homer"'
        //     }
        // }
        // // trigger portainer redeploy
        // // separated out so this only gets run if the ansible playbook doesn't fail
        // stage('redeploy portainer stack (PRD)') {
        //     when { branch 'master' }
        //     steps {
        //         // deploy configs to DEV
        //         echo 'Redeploy PRD stack'
        //         sh 'http post ${PORTAINER_PRD_WEBHOOK}'
        //     }
        // }

    }
    post {
        always {
            discordSend \
                description: "${JOB_NAME} - build #${BUILD_NUMBER}", \
                // footer: "Footer Text", \
                // link: env.BUILD_URL, \
                result: currentBuild.currentResult, \
                // title: JOB_NAME, \
                webhookURL: "${WEBHOOK}"
        }
    }
}

