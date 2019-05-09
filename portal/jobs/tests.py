from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files import File

from .models import Job
from .celery import run_job_docker

import time


class JobHelloWorldIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user('toejam', 'toejam@funkotron.net', 'toejam')
        file = File(open('tests/hello.tar.gz', 'rb'))
        self.job = Job.objects.create(
            name='Hello Job',
            description='Return output with Hello World text',
            status=Job.Status.QUEUED.name,
            owner=self.creator,
            filename=file.name,
            file=file,
            submitted_at=timezone.now(),
        )

    def test_hello_completes(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status_enum, Job.Status.PENDING_OUTPUT_REVIEW)

    def test_hello_has_output(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertTrue('Hello from Docker!' in self.job.output.read().decode('utf-8'))

    def test_hello_has_no_error(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertFalse(getattr(self.job, 'errors', None))

    def test_hello_not_failed(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertFalse(self.job.failed)

class JobGoodbyeWorldIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user('toejam', 'toejam@funkotron.net', 'toejam')
        file = File(open('tests/goodbye.tar.gz', 'rb'))
        self.job = Job.objects.create(
            name='Goodbye Job',
            description='Return error with Goodbye World text',
            status=Job.Status.QUEUED.name,
            owner=self.creator,
            filename=file.name,
            file=file,
            submitted_at=timezone.now(),
        )

    def test_goodbye_completes(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status_enum, Job.Status.PENDING_OUTPUT_REVIEW)

    def test_goodbye_has_error(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertTrue('Goodbye' in self.job.errors.read().decode('utf-8'))

    def test_goodbye_has_no_output(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertFalse(getattr(self.job, 'output', None))

    def test_goodbye_failed(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertTrue(self.job.failed)

class JobAccessInternetIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user('toejam', 'toejam@funkotron.net', 'toejam')
        file = File(open('tests/access-internet.tar.gz', 'rb'))
        self.job = Job.objects.create(
            name='Access Internet Job',
            description='Return error with failure of access-internet to connect',
            status=Job.Status.QUEUED.name,
            owner=self.creator,
            filename=file.name,
            file=file,
            submitted_at=timezone.now(),
        )

    def test_access_internet_completes(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status_enum, Job.Status.PENDING_OUTPUT_REVIEW)

    def test_access_internet_has_error(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        message = self.job.errors.read().decode('utf-8')
        self.assertTrue('Could not resolve' in message or 'timed out' in message)

    def test_access_internet_has_no_output(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertFalse(getattr(self.job, 'output', None))

    def test_access_internet_failed(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertTrue(self.job.failed)

# export JOB_RESOURCES=104.40.211.35,98.137.246.8  before starting docker-compose
class JobAccessResourceIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user('toejam', 'toejam@funkotron.net', 'toejam')
        file = File(open('tests/access-resource.tar.gz', 'rb'))
        self.job = Job.objects.create(
            name='Access Resource Job',
            description='Return success of access-resource connection',
            status=Job.Status.QUEUED.name,
            owner=self.creator,
            filename=file.name,
            file=file,
            submitted_at=timezone.now(),
        )

    def test_access_resource_completes(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status_enum, Job.Status.PENDING_OUTPUT_REVIEW)

    def test_access_resource_has_output(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        message = self.job.output.read().decode('utf-8')
        # print(message)
        self.assertTrue('html' in message)

    def test_access_resource_has_no_error(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        error = getattr(self.job, 'error', None)
        print(error)
        self.assertFalse(error)

    def test_access_resource_not_failed(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertFalse(self.job.failed)

class JobEnvVarsIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user('toejam', 'toejam@funkotron.net', 'toejam')
        file = File(open('tests/env-vars.tar.gz', 'rb'))
        self.job = Job.objects.create(
            name='Env Vars Job',
            description='Return env vars, including those inserted by the Portal',
            status=Job.Status.QUEUED.name,
            owner=self.creator,
            filename=file.name,
            file=file,
            submitted_at=timezone.now(),
        )

    def test_env_var_completes(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status_enum, Job.Status.PENDING_OUTPUT_REVIEW)

    def test_env_var_has_var(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        message = self.job.output.read().decode('utf-8')
        # print(message)
        self.assertTrue('EXAMPLE_VAR=abcd1234' in message)

    def test_env_var_has_no_error(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        error = getattr(self.job, 'error', None)
        print(error)
        self.assertFalse(error)

    def test_env_var_not_failed(self):
        run_job_docker(self.job)
        self.job.refresh_from_db()
        self.assertFalse(self.job.failed)
