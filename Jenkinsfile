node {

    //triggering periodically so the code is always present
    // run every friday at 3AM
    // triggers { cron('0 3 * * 5') }

    try {
        def app

        // ensure we have the code
        stage('Clone repository') {
            checkout scm
        }

        stage("Build ${env.BRANCH_NAME} image") {
            if (env.BRANCH_NAME == 'dev_test') {
                app = docker.build("drak3/hu3bot-dev")
            }

            if (env.BRANCH_NAME == 'master') {
                app = docker.build("drak3/hu3bot")
            }
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
            docker.withRegistry('https://registry.hub.docker.com', 'DOCKER_HUB_CREDENTIALS') {
            // docker.withRegistry('https://registry.hub.docker.com') {
                app.push("${env.BUILD_NUMBER}")
                app.push("latest")
            }
        }

        stage('Notifier') {
            discordSend \
                description: "${JOB_NAME} - build #${BUILD_NUMBER}", \
                // footer: "Footer Text", \
                // link: env.BUILD_URL, \
                result: currentBuild.currentResult, \
                // title: JOB_NAME, \
                webhookURL: 'JENKINS_DISCORD'
        }
    }

    



    // finally {
    //     discordSend \
    //         description: "${JOB_NAME} - build #${BUILD_NUMBER}", \
    //         // footer: "Footer Text", \
    //         // link: env.BUILD_URL, \
    //         result: currentBuild.currentResult, \
    //         // title: JOB_NAME, \
    //         webhookURL: 'JENKINS_DISCORD'
    
    // }
}

