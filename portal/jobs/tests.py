import json
import base64

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from .views import complete_job, fail_job
from .models import Job

@override_settings(RUNNER_KEY='TEST')
class CompleteViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user('toejam', 'toejam@funkotron.net', 'toejam')
        self.job = Job.objects.create(
                name='A Test Job',
                description='Do many testful things and return output.',
                status=Job.Status.RUNNING.name,
                owner=self.creator,
                filename='test.txt',
                file=ContentFile('test input'),
                submitted_at=timezone.now(),
            )

    def test_responds_401_if_key_empty(self):
        data = {
            'id': self.job.id,
            'output': str(base64.b64encode(b'test test test')),
            'key': '',
        }
        resp = self.client.post(reverse('jobs:complete'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_responds_401_if_key_missing(self):
        data = {
            'id': self.job.id,
            'output': str(base64.b64encode(b'test test test')),
        }
        resp = self.client.post(reverse('jobs:complete'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_responds_401_if_key_not_matching(self):
        data = {
            'id': self.job.id,
            'output': str(base64.b64encode(b'test test test')),
            'key': 'test', # Should be upper case
        }
        resp = self.client.post(reverse('jobs:complete'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_responds_400_if_json_malformed(self):
        data = f"{{'id' 0,'output': 'test output','key': 'test'}}" # Missing colon after 'id'
        resp = self.client.post(reverse('jobs:complete'), data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_completes_job(self):
        data = {
            'id': self.job.id,
            'output': str(base64.b64encode(b'test test test')),
            'key': 'TEST',
        }
        resp = self.client.post(reverse('jobs:complete'), data=json.dumps(data), content_type='application/json')
        self.job.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(hasattr(self.job, 'output'))
        self.assertEqual(self.job.status_enum(), Job.Status.PENDING_OUTPUT_REVIEW)


@override_settings(RUNNER_KEY='TEST')
class FailViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user('toejam', 'toejam@funkotron.net', 'toejam')
        self.job = Job.objects.create(
                name='A Test Job',
                description='Do many testful things and return output.',
                status=Job.Status.RUNNING.name,
                owner=self.creator,
                filename='test.txt',
                file=ContentFile('test input'),
                submitted_at=timezone.now(),
            )

    def test_responds_401_if_key_empty(self):
        data = {
            'id': self.job.id,
            'output': str(base64.b64encode(b'test test test')),
            'key': '',
        }
        resp = self.client.post(reverse('jobs:fail'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_responds_401_if_key_missing(self):
        data = {
            'id': self.job.id,
            'output': str(base64.b64encode(b'test test test')),
        }
        resp = self.client.post(reverse('jobs:fail'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_responds_401_if_key_not_matching(self):
        data = {
            'id': self.job.id,
            'output': str(base64.b64encode(b'test test test')),
            'key': 'test', # Should be upper case
        }
        resp = self.client.post(reverse('jobs:fail'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_responds_400_if_json_malformed(self):
        data = f"{{'id' 0,'output': 'test output','key': 'test'}}" # Missing colon after 'id'
        resp = self.client.post(reverse('jobs:fail'), data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_fails_job(self):
        data = {
            'id': self.job.id,
            'output': str(base64.b64encode(b'test test test')),
            'key': 'TEST',
        }
        resp = self.client.post(reverse('jobs:fail'), data=json.dumps(data), content_type='application/json')
        self.job.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.job.status_enum(), Job.Status.PENDING_OUTPUT_REVIEW)
        self.assertEqual(self.job.failed, True)


@override_settings(RUNNER_KEY='TEST')
class StartViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user('toejam', 'toejam@funkotron.net', 'toejam')
        self.job = Job.objects.create(
                name='A Test Job',
                description='Do many testful things and return output.',
                status=Job.Status.QUEUED.name,
                owner=self.creator,
                filename='test.txt',
                file=ContentFile('test input'),
                submitted_at=timezone.now(),
            )

    def test_responds_401_if_key_empty(self):
        data = {
            'id': self.job.id,
            'key': '',
        }
        resp = self.client.post(reverse('jobs:start'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_responds_401_if_key_missing(self):
        data = {
            'id': self.job.id,
        }
        resp = self.client.post(reverse('jobs:start'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_responds_401_if_key_not_matching(self):
        data = {
            'id': self.job.id,
            'key': 'test', # Should be upper case
        }
        resp = self.client.post(reverse('jobs:start'), data=json.dumps(data), content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_responds_400_if_json_malformed(self):
        data = f"{{'id' 0,'key': 'test'}}" # Missing colon after 'id'
        resp = self.client.post(reverse('jobs:start'), data=data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_job_running(self):
        data = {
            'id': self.job.id,
            'key': 'TEST',
        }
        resp = self.client.post(reverse('jobs:start'), data=json.dumps(data), content_type='application/json')
        self.job.refresh_from_db()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.job.status_enum(), Job.Status.RUNNING)


class RunnerIntegrationTests(TestCase):

    def setUp(self):
        key = getattr(settings, 'RUNNER_KEY', '')
        if not key.strip():
            raise Exception('Set RUNNER_KEY in environment and run this test with docker-compose.')
        self.client = Client()
        self.creator = User.objects.create_user('toejam', 'toejam@funkotron.net', 'toejam')
        self.job = Job.objects.create(
                name='A Test Job',
                description='Do many testful things and return output.',
                status=Job.Status.PENDING_CODE_REVIEW.name,
                owner=self.creator,
                filename='test.txt',
                file=SimpleUploadedFile('test.txt', b'test test test'),
                submitted_at=timezone.now(),
            )
        self.job.save()

    def test_enqueue_integrates(self):
        self.job.approve_code()
        self.job.save()
        self.job.refresh_from_db()
        self.assertEqual(self.job.status_enum(), Job.Status.QUEUED)

    @override_settings(RUNNER_KEY='mismatch')
    def test_enqueue_fails_if_key_mismatch(self):
        with self.assertRaises(Exception):
            self.job.approve_code()
