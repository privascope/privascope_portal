import enum
import base64
import time
import os

from django.db import models
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.conf import settings
from django.urls import reverse
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

from django_fsm import FSMField, transition
from django_fsm_log.decorators import fsm_log_by

import requests


private_storage = FileSystemStorage(location=settings.PRIVATE_STORAGE_ROOT)


class Job(models.Model):
    class Status(enum.Enum):
        DELETED = {
            'code': 0,
            'label': 'Deleted',
            'is_failure': True,
            'is_success': False,
        }
        PENDING_CODE_REVIEW = {
            'code': 10,
            'label': 'Pending Code Review',
            'is_failure': False,
            'is_success': False,
        }
        CODE_REJECTED = {
            'code': 11,
            'label': 'Code Rejected',
            'is_failure': True,
            'is_success': False,
        }
        QUEUED = {
            'code': 20,
            'label': 'Queued',
            'is_failure': False,
            'is_success': False,
        }
        QUEUED_ERROR = {
            'code': 21,
            'label': "Queue Failed",
            'is_failure': True,
            'is_success': False,
        }
        RUNNING = {
            'code': 30,
            'label': 'Running',
            'is_failure': False,
            'is_success': False,
        }
        RUN_ERROR = {
            'code': 31,
            'label': 'Failed Run',
            'is_failure': True,
            'is_success': False,
        }
        PENDING_OUTPUT_REVIEW = {
            'code': 40,
            'label': 'Pending Output Review',
            'is_failure': False,
            'is_success': False,
        }
        OUTPUT_REJECTED = {
            'code': 41,
            'label': 'Output Rejected',
            'is_failure': True,
            'is_success': False,
        }
        RELEASED = {
            'code': 50,
            'label': 'Released',
            'is_failure': False,
            'is_success': True,
        }

        def choices(self):
            return ((e.name, e.value['label']) for e in self if type(e) is object)

    # Workaround to navigate into the class in Django templates
    # rather than executing it as a constructor
    Status.do_not_call_in_templates = True

    name = models.CharField(verbose_name='Title', max_length=64, help_text='Write a short, descriptive title that will help you identify this request.')
    description = models.CharField(verbose_name='Description', max_length=1000, help_text='Provide a brief description of your request and any important notes for the review team.')
    submitted_at = models.DateTimeField(verbose_name='Submitted At', auto_now_add=True)
    status = FSMField(
        default=Status.PENDING_CODE_REVIEW.name,
        verbose_name='Status',
        choices=Status.choices(Status),
        #protected=True, # Not compatible with refresh_from_db, which is used in tests
        editable=False,
    )
    failed = models.BooleanField(verbose_name='Failed', default=False)
    owner = models.ForeignKey(User, verbose_name='Owner', related_name='owned', on_delete=models.PROTECT)
    filename = models.CharField(verbose_name='Filename',  max_length=64)
    file = models.FileField(storage=private_storage, verbose_name='File', help_text='Submit a ZIP file containing your code, a dockerfile, and README file. See Getting Started for more information.')
    collaborators = models.ManyToManyField(User, verbose_name='Collaborators', related_name='collaborating', blank=True, help_text='Collaborators will be able to check and update the request and download the data. Currently, only individuals with a U-M account may be added as collaborators.')
    output = models.FileField(storage=private_storage, verbose_name='Output', blank=True)
    errors = models.FileField(storage=private_storage, verbose_name='Errors', blank=True)

    def output_filename(self):
        return os.path.basename(self.output.file.name)

    def errors_filename(self):
        return os.path.basename(self.errors.file.name)

    @property
    def status_enum(self):
        return self.Status[self.status]

    @property
    def is_released(self):
        return self.status_enum is self.Status.RELEASED

    def status_badge(self):
        return status_type_badges[self.status_enum]

    def can_view(self, user):
        return user.is_staff or user == self.owner or user in self.collaborators.all()

    def _enqueue(self):
        try:
            from .celery import task_run_job
            task_run_job.apply_async(countdown=10, args=[self.id])
        except Exception:
            self._queue_failed()
            raise

    @fsm_log_by
    @transition(field=status, source=Status.QUEUED.name, target=Status.QUEUED_ERROR.name)
    def queue_failed(self, by=None):
        pass

    @fsm_log_by
    @transition(field=status, source=Status.PENDING_CODE_REVIEW.name, target=Status.QUEUED.name)
    def approve_code(self, by=None):
        self._enqueue()

    @fsm_log_by
    @transition(field=status, source=Status.PENDING_CODE_REVIEW.name, target=Status.CODE_REJECTED.name)
    def reject_code(self, by=None):
        pass

    @fsm_log_by
    @transition(field=status, source=Status.QUEUED.name, target=Status.RUNNING.name)
    def run_job(self, by=None):
        pass

    @fsm_log_by
    @transition(field=status, source=Status.RUNNING.name, target=Status.RUN_ERROR.name)
    def error_job_run(self, by=None):
        pass

    @transition(field=status, source=Status.RUNNING.name, target=Status.PENDING_OUTPUT_REVIEW.name)
    def complete_job_run(self, output=None, errors=None):
        if output:
            self.output.save(f'{self.id}-{int(time.time())}.out', ContentFile(output))
        if errors:
            self.errors.save(f'{self.id}-{int(time.time())}.err', ContentFile(errors))

    @transition(field=status, source=Status.RUNNING.name, target=Status.PENDING_OUTPUT_REVIEW.name)
    def fail_job_run(self, output=None, errors=None):
        self.failed = True
        if output:
            self.output.save(f'{self.id}-{int(time.time())}.out', ContentFile(output))
        if errors:
            self.errors.save(f'{self.id}-{int(time.time())}.err', ContentFile(errors))

    @fsm_log_by
    @transition(field=status, source=Status.PENDING_OUTPUT_REVIEW.name, target=Status.RELEASED.name)
    def approve_output(self, by=None):
        pass

    @fsm_log_by
    @transition(field=status, source=Status.PENDING_OUTPUT_REVIEW.name, target=Status.OUTPUT_REJECTED.name)
    def reject_output(self, by=None):
        pass

    @fsm_log_by
    @transition(field=status, source=Status.PENDING_CODE_REVIEW.name, target=Status.DELETED.name)
    def delete_job(self, by=None):
        pass

    def __str__(self):
        return f'<Job {self.id}:{self.name}:{self.submitted_at}:{self.owner}:{self.filename}:{self.status}>'


class Comment(models.Model):
    job = models.ForeignKey(Job, verbose_name='Job', related_name='comments', on_delete=models.CASCADE)
    text = models.CharField(verbose_name='Text', max_length=1024)
    by = models.ForeignKey(User, verbose_name='By', on_delete=models.PROTECT)
    timestamp = models.DateTimeField(verbose_name='Timestamp', auto_now_add=True)

    def __str__(self):
        return f'{self.job.id}@{self.timestamp}-- {self.by}: {self.text}'


status_type_badges = {
    Job.Status.DELETED: 'dark',
    Job.Status.PENDING_CODE_REVIEW: 'secondary',
    Job.Status.CODE_REJECTED: 'danger',
    Job.Status.QUEUED: 'info',
    Job.Status.QUEUED_ERROR: 'danger',
    Job.Status.RUNNING: 'info',
    Job.Status.RUN_ERROR: 'danger',
    Job.Status.PENDING_OUTPUT_REVIEW: 'warning',
    Job.Status.OUTPUT_REJECTED: 'danger',
    Job.Status.RELEASED: 'success',
}

import jobs.signals
