# Deployment

Django is only a web framework it cannot run without a web server and a database. Django needs a WSGI server to run the Python code. We use `uWSGI`. `uWSGI` needs a webserver that handles the web traffic, for this we use `NGINX` (which also handles all the static files). In development a simple SQLite3 database is used, because it is easy to setup and easy to delete. In production a more robust solution is necessary, that is why Postgres is used as production database.

- [Docker](#docker)
  - [Dockerfile](#dockerfile)
  - [Entrypoint](#entrypoint)
  - [GitHub Packages](#github-packages)
  - [Docker Compose](#docker-compose)
    - [`nginx`](#nginx)
    - [`letsencrypt`](#letsencrypt)
    - [`postgres`](#postgres)
    - [`web`](#web)
- [Deployment Pipeline](#deployment-pipeline)
  - [`deploy.yaml` workflow](#deployyaml-workflow)
    - [`build-docker` job](#build-docker-job)
    - [`deploy` job](#deploy-job)
  - [Secrets](#secrets)
- [Server Configuration](#server-configuration)
- [Keeping Everything Up to Date](#keeping-everything-up-to-date)

## Docker
The website is meant to be run as a Docker container on a Linux server. The use of Docker containers, allows us to create a tailor-made environment (a Docker image) that has all the dependencies (i.e. files, libraries and packages) pre-installed. 

### Dockerfile
The [Dockerfile](https://docs.docker.com/engine/reference/builder/) which steps should be executed to create the Docker image. This Docker image has all dependencies and the source code of the website. It also specifies that the production settings should be used.

### Entrypoint
The entrypoint (`/usr/local/bin/entrypoint.sh` inside the Docker image) is executed whenever a container is created from the Docker image, it waits for the Postgres database to come up, makes the necessary changes to the static files and the database, creates a superuser (if it does not exist yet) and starts `uWSGI`.

### GitHub Packages
A Docker image of the website ([docker.pkg.github.com/giphouse/website/production](https://github.com/GipHouse/Website/packages/356257)) is available on GitHub Packages. This image is refreshed every time a change is merged into the `master` branch.

### Docker Compose
`docker-compose` is a tool that allows us to run multiple Docker containers that are connected to make them work together. Please see the [`docker-compose.yaml`](../resources/docker-compose.yaml.template) file for the exact settings. This file contains all the configuration to pass the correct environment variables to the containers and save the correct files to the host.  

The following services are created by `docker-compose`.

#### `nginx`
[`nginx-proxy`](https://github.com/jwilder/nginx-proxy) is a Docker image containing that automatically generates correct `NGINX` configuration for other Docker Images. It listens on port 80 (HTTP) and 443 (HTTPS) and acts as the main access point for all web traffic to the website.

#### `letsencrypt`
[`letsencrypt-nginx-proxy-companion`](https://github.com/JrCs/docker-letsencrypt-nginx-proxy-companion) is a Docker image that uses Let's Encrypt to request a TLS certificate to make the website available over HTTPS.`

#### `postgres`
Runs a Postgres Database.

#### `web`
[`giphouse/giphousewebsite`](https://hub.docker.com/r/giphouse/giphousewebsite) is the Docker image that runs the actual website using `gunicorn` as server.

## Deployment Pipeline
### `deploy.yaml` workflow
Whenever a change is merged into the `master` branch, the `deploy.yaml` GitHub Actions workflow is run. This workflow does the following:

#### `build-docker` job
1. Build a Docker image using the `master` branch.
2. Push the Docker image to GitHub Packages.

#### `deploy` job
After the `build-docker` job is finished, the `deploy` job runs.
1. Sets up SSH key that allows the runner to login to the production server using SSH.
2. Fills in passwords and secrets in the necessary files.
3. Create the necessary directories and files on the production server.
4. Pulls the new Docker image.
5. Restarts the production website with the new Docker image.
6. Purge all old unused Docker images.

### Secrets
This repository is public and the GitHub Actions CI runner logs are also public, but some deployment information is secret. The secret information is setup using [GitHub repository secrets](https://help.github.com/en/actions/automating-your-workflow-with-github-actions/creating-and-using-encrypted-secrets). These are passed as environment variables to the GitHub Actions CI runners. The following secrets are setup.
- `DJANGO_SECRET_KEY`: The [`SECRET_KEY`](https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-SECRET_KEY) for Django.
- `DJANGO_GITHUB_SYNC_APP_ID`: The App ID of the registered GitHub App installed in the GiPHouse organization.
- `DJANGO_GITHUB_SYNC_APP_PRIVATE_KEY_BASE64`: The private RSA key ([PEM formatted](https://en.wikipedia.org/wiki/Privacy-Enhanced_Mail)) of the registered GitHub App installed in the GiPHouse organization, `base64` encoded.
- `DJANGO_GITHUB_SYNC_APP_INSTALLATION_ID`: The Installation ID of the registered GitHub App installed in the GiPHouse organization.
- `DJANGO_GITHUB_SYNC_ORGANIZATION_NAME`: The name of the organization the registered GitHub App is installed in.
- `DJANGO_GITHUB_CLIENT_ID`: The GiPHouse organization GitHub (OAuth) App client ID.
- `DJANGO_GITHUB_CLIENT_SECRET`: The GiPHouse organization GitHub (OAuth) App client secret key.
- `DJANGO_GITHUB_SYNC_SUPERUSER_ID`: The Github ID of the initial superuser.
- `DJANGO_GSUITE_ADMIN_USER`: The user which the G Suite api will impersonate when logging in with the credentials.
- `DJANGO_GSUITE_ADMIN_CREDENTIALS_BASE64`: The G Suite service account key file in json format, then `base64` encoded.
- `POSTGRES_NAME`: The name of the Postgres database.
- `POSTGRES_USER`: The username that is used to interact with the Postgres database.
- `POSTGRES_PASSWORD`: The password that is used to interact with the Postgres database.
- `SSH_USER`: The user that the CI runner uses to login to the production server using SSH. This user should be allowed to use Docker (e.g. be a member of the `docker` group).
- `SSH_PRIVATE_KEY`: The private key that allows the `SSH_USER` user to login to the production server using SSH.

## Server Configuration
The current server is an Amazon Web Services Elastic Cloud Computing (AWS EC2) instance that runs Ubuntu 18.04. EC2 instances have a default `ubuntu` user, that is allowed to execute `sudo` without password. The `docker-compose.yaml` file includes all services that are necessary to run the website in a production environment. That is why Docker is the only dependency on the host.

These steps are the necessary setup for a production server.
1. Add the SSH public keys of engineers to the `authorized_keys` of the `ubuntu` user.
2. Disable SSH password login.
3. Install `docker` and `docker-compose`.
4. Add the `ubuntu` user to the `docker` group.
5. Add the public key of the `SSH_PRIVATE_KEY` GitHub secret to the `authorized_keys` file of the `SSH_USER` GitHub secret user.
6. Change the url of the website by changing the `DEPLOYMENT_HOST` env variable in the deploy.yaml file. This will set the host in all necessary places.

## Keeping Everything Up to Date
All moving parts should be regularly updated to make sure all code is up to date and secure. There is no process in place to automate updates, because that may break something.
The following items should be taken into account:

1. The Ubuntu server should be updated.
2. The Python dependencies should be updated (through `uv`).
3. The JavaScript, font and [S]CSS files should be updated by replacing the current files with new ones.
