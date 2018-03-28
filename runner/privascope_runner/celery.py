import os
import time
import base64
import tempfile
import tarfile
from subprocess import check_output

from django.conf import settings

from celery import Celery
import requests
import docker
from tenacity import retry, stop_after_attempt, wait_exponential


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'privascope_runner.settings')

app = Celery('privascope_runner')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# @app.task(bind=True)
# def debug_task(self):
#     print('Request: {0!r}'.format(self.request))

@app.task(bind=True)
def run_job(self, job):
    key = settings.RUNNER_KEY
    _send_run_started(key, job['id'])
    exit_code, encoded_output, encoded_errors = _build_run_job(job['file'])
    if exit_code != 0:
        _send_run_failed(key, job['id'], encoded_output, encoded_errors)
    else:
        _send_run_completed(key, job['id'], encoded_output, encoded_errors)

@retry(stop=stop_after_attempt(5), wait=wait_exponential(1, 30))
def _send_run_started(key, job_id):
    start_url = settings.PORTAL_URL_BASE + settings.PORTAL_START
    start_payload = {
        'key': key,
        'id': job_id,
    }
    resp = requests.post(start_url, json=start_payload)
    if resp.status_code != 200:
        resp.raise_for_status()

def _build_run_job(job_file_b64):
    with tempfile.TemporaryDirectory() as job_dir:
        with tempfile.NamedTemporaryFile() as job_file:
            job_file.write(base64.b64decode(job_file_b64))
            job_file.flush()
            job_file.seek(0)
            job_tar = tarfile.open(job_file.name, 'r|gz')
            job_tar.extractall(path=job_dir) # Can create files outside of path. How to secure?
            docker_client = docker.from_env()
            image, build_log_generator = docker_client.images.build(path=job_dir, rm=True)

    container = docker_client.containers.run(image.id, detach=True)
    container_result = container.wait()
    container_output = container.logs(stdout=True, stderr=False)
    container_errors = container.logs(stderr=True, stdout=False)
    container.remove()
    container_exit_code = container_result['StatusCode']
    return container_exit_code, base64.b64encode(container_output).decode('utf8'), base64.b64encode(container_errors).decode('utf8')

@retry(stop=stop_after_attempt(5), wait=wait_exponential(1, 30))
def _send_run_completed(key, job_id, job_stdout, job_stderr):
    complete_url = settings.PORTAL_URL_BASE + settings.PORTAL_COMPLETE
    complete_payload = {
        'key': key,
        'id': job_id,
        'output': job_stdout,
        'errors': job_stderr,
    }
    resp = requests.post(complete_url, json=complete_payload)
    if resp.status_code != 200:
        resp.raise_for_status()

@retry(stop=stop_after_attempt(5), wait=wait_exponential(1, 30))
def _send_run_failed(key, job_id, job_stdout, job_stderr):
    failed_url = settings.PORTAL_URL_BASE + settings.PORTAL_FAIL
    failed_payload = {
        'key': key,
        'id': job_id,
        'output': job_stdout,
        'errors': job_stderr,
    }
    resp = requests.post(failed_url, json=failed_payload)
    if resp.status_code != 200:
        resp.raise_for_status()
