## Tariff Tribe - Deployment

The web application is designed to be built and run within a Docker container. The [Dockerfile](../Dockerfile) contains a production-ready build configuration for the container to run the tariff tribe application.

To aid in building and running the container, a [docker-compose.yml](../compose.yml) is also provided which passes in the environment variables from the `.env` file.

## Continuous Deployment (CD)

TBD - create GitHub action to build the docker container and deploy the application See [here](https://docs.servicestack.net/ssh-docker-compose-deploment#understanding-the-core-components) for inspiration.
