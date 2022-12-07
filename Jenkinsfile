node {


    def app

    // ensure we have the code
    stage('Clone repository') {
        checkout scm
    }

    // not going to use multi branches for automated deployment
    // stage("Build ${env.BRANCH_NAME} image") {
    //     if (env.BRANCH_NAME == 'dev_test') {
    //         app = docker.build("drak3/hu3bot-dev")
    //     }
    //     if (env.BRANCH_NAME == 'master') {
    //         app = docker.build("drak3/hu3bot")
    //     }
    // }

    stage("Build ${env.BRANCH_NAME} image") {
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
        docker.withRegistry('https://registry.hub.docker.com', 'DOCKER_HUB_CREDENTIALS') {
            app.push("${env.BUILD_NUMBER}")
            app.push("latest")
        }
    }

    // portainer webhook
    stage("Deploy") {
            // sh 'http post ${PORTAINER_PRD_WEBHOOK}'
            // sh 'http post ${PORTAINER_WEBHOOK_DEV_HU3BOT}'
        httpRequest httpMode: 'POST'
                    url: '${PORTAINER_WEBHOOK_DEV_HU3BOT}'
    }

}

