import os
import time
import base64
import tempfile
import tarfile
from subprocess import check_output
from pathlib import Path

from django.conf import settings

from celery import Celery
import requests
import docker


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'privascope_portal.settings')

app = Celery('jobs')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

import django
django.setup()
from .models import Job


@app.task(bind=True)
def task_run_job(self, job_id):
    job = Job.objects.get(pk=job_id)
    run_job_docker(job)

def run_job_docker(job):
    _run_started(job)
    exit_code, encoded_output, encoded_errors = _build_run_job(base64.b64encode(job.file.file.read()).decode('utf8'))
    if exit_code != 0:
        _run_failed(job, encoded_output, encoded_errors)
    else:
        _run_completed(job, encoded_output, encoded_errors)

def _run_started(job):
    job.run_job()
    job.save()

def _run_completed(job, job_stdout, job_stderr):
    job.complete_job_run(job_stdout, job_stderr)
    job.save()

def _run_failed(job, job_stdout, job_stderr):
    job.fail_job_run(job_stdout, job_stderr)
    job.save()

def _build_image(job_file_bytes, docker_client):
    with tempfile.TemporaryDirectory() as job_dir:
        with tempfile.NamedTemporaryFile() as job_file:
            job_file.write(job_file_bytes)
            job_file.flush()
            job_file.seek(0)
            job_tar = tarfile.open(job_file.name, 'r|gz')
            job_tar.extractall(path=job_dir) # Can create files outside of path. How to secure?
            # If there's no Dockerfile, try navigating into the first directory to find it
            if not Path(os.path.join(job_dir, 'Dockerfile')).is_file():
                job_dir = os.path.join(job_dir, os.listdir(job_dir)[0])
            try:
                image, build_log_generator = docker_client.images.build(path=job_dir, rm=True)
                return image
            except docker.errors.APIError as ex:
                print(ex)
                raise ex

def _build_run_job(job_file_b64):
    docker_client = docker.from_env()
    job_file_bytes = base64.b64decode(job_file_b64)
    image = _build_image(job_file_bytes, docker_client)
    container = docker_client.containers.run(image.id, detach=True, network='job-network')
    container_result = container.wait()
    container_output = container.logs(stdout=True, stderr=False)
    container_errors = container.logs(stderr=True, stdout=False)
    container.remove()
    container_exit_code = container_result['StatusCode']
    return container_exit_code, container_output, container_errors
