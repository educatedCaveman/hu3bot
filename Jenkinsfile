node {


    environment {
        ANSIBLE_REPO = '/var/lib/jenkins/workspace/ansible_master'
        WEBHOOK = credentials('JENKINS_DISCORD')
        PORTAINER_DEV_WEBHOOK = credentials('PORTAINER_WEBHOOK_DEV_HU3BOT')
        PORTAINER_PRD_WEBHOOK = credentials('PORTAINER_WEBHOOK_PRD_HU3BOT')
        DOCKER_CREDENTIALS = credentials('DOCKER_HUB_CREDENTIALS')
    }

    //triggering periodically so the code is always present
    // run every friday at 3AM
    // triggers { cron('0 3 * * 5') }


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

