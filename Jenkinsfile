node {


    def app

    // ensure we have the code
    stage('Clone repository') {
        checkout scm
    }

    stage("Build Docker image") {
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
        // TODO: fix the issue of not being able to use the webhook credential
        httpRequest httpMode: 'POST',
                    // url: 'PORTAINER_WEBHOOK_PRD_HU3BOT'
                    url: 'https://portainer.drak3.io/api/stacks/webhooks/167564ee-cf7a-4221-abd1-3a28bda6db28'
    }

}

