# PrivaScope Portal

PrivaScope Portal provides a web interface and backing infrastructure by which Docker-based jobs can be submitted and run with access to secure resources. It enforces a workflow requiring review of the input code and also of the output results.

The web interface is a Django app employing django_fsm for workflow actions. Celery is used to execute jobs on a Docker daemon with a whitelist of permitted network resources.

## Development

### Setup for docker-compose

Customize and run the following for required environment variables. In Windows, you may need to use [Powershell](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_environment_variables?view=powershell-6):

    export PRIVATE_STORAGE_ROOT="files/"
    export SAML2_SP_CERT=(SAML2 SP certificate)
    export SAML2_SP_KEY=(SAML2 SP key)
    export SAML2_IDP_METADATA=(SAML2 IDP metadata)
    export SAML2_SP_NAME="Example SP Name"
    export SAML2_LS_REDIRECT=https://example.com/saml/ls/
    export SAML2_LS_POST=https://example.com/saml/ls/post
    export SAML2_ACS_POST=https://example.com/saml/acs/
    export SAML2_REQUIRED_ATTRIBUTES=username,email
    export SAML2_OPTIONAL_ATTRIBUTES=roles,address
    export RUNNER_KEY=random_password
    export RUNNER_QUEUE_USER=admin
    export RUNNER_QUEUE_PASS=random_password
    export RUNNER_WORKER_LOGLEVEL=debug
    export SECRET_KEY_RUNNER=random_password
    export SECRET_KEY_PORTAL=random_password
    export EMAIL_HOST=smtp.gmail.com
    export EMAIL_HOST_USER=test.email.account@gmail.com
    export EMAIL_HOST_PASSWORD=random_password
    export EMAIL_PORT=587
    export EMAIL_USE_TLS=True
    export DEBUG=yes
    export ABSOLUTE_URL_BASE=http://localhost:8023
    # Microsoft.com & Yahoo.com, respectively - include these as-is for integration tests
    export JOB_RESOURCES=104.40.211.35,98.137.246.8,microsoft.com,yahoo.com
    export JOB_ENV_VARS="EXAMPLE_VAR=abcd1234"

Do initial setup:

    docker-compose build
    docker-compose up --no-start
    docker-compose start
    docker-compose run portal python3.6 manage.py migrate
    docker-compose stop

Start the development environment:

    docker-compose up

You can now test the app at localhost:8023.

#### Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?

If you encounter this error on startup:

    docker-compose rm
    docker-compose up

This should get the daemon running again.

### Integration tests

1. Run the app with docker-compose as described above.
2. `docker-compose run portal python3.6 manage.py test`
