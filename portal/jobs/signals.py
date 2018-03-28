from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.mail import EmailMessage, mail_admins
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User

from django_fsm.signals import pre_transition, post_transition

from .models import Job

@receiver(post_save, sender=Job)
def send_job_created_email(sender, instance, created, **kwargs):
    if not created:
        return
    staff = User.objects.filter(is_staff=True)
    to = (s.email for s in staff)
    subject = f'Job Awaiting Code Review: {instance.name}'
    url = settings.ABSOLUTE_URL_BASE + reverse('jobs:detail', args=(instance.id,))
    body = f'User {instance.owner.username} created job <a href="{url}">{instance.id} ({instance.name})</a>. It is now awaiting code review.'
    email = EmailMessage(subject, body, to=to)
    email.content_subtype = "html"
    email.send()

def email_approve_code(job):
    to = [job.owner.email]
    cc = (c.email for c in job.collaborators.all())
    subject = f'Code Approved: {job.name}'
    url = settings.ABSOLUTE_URL_BASE + reverse('jobs:detail', args=(job.id,))
    link = f'<a href="{url}">{job.id} ({job.name})</a>'
    body = f'Your job {link} was approved and is now queued to run in the PrivaScope Enclave.'
    email = EmailMessage(subject, body, to=to, cc=cc)
    email.content_subtype = "html"
    email.send()

def email_reject_code(job):
    to = [job.owner.email]
    cc = (c.email for c in job.collaborators.all())
    subject = f'Code Rejected: {job.name}'
    url = settings.ABSOLUTE_URL_BASE + reverse('jobs:detail', args=(job.id,))
    link = f'<a href="{url}">{job.id} ({job.name})</a>'
    body = f'Your job {link} was rejected. <a href={url}>Click here</a> to read what steps to take next.'
    email = EmailMessage(subject, body, to=to, cc=cc)
    email.content_subtype = "html"
    email.send()

def email_complete_job_run(job):
    to = [job.owner.email]
    cc = (c.email for c in job.collaborators.all())
    subject = f'Job Run Completed: {job.name}'
    url = settings.ABSOLUTE_URL_BASE + reverse('jobs:detail', args=(job.id,))
    link = f'<a href="{url}">{job.id} ({job.name})</a>'
    body = f'Your job {link} was completed. Its output is now pending review.'
    email = EmailMessage(subject, body, to=to, cc=cc)
    email.content_subtype = "html"
    email.send()

def email_fail_job_run(job):
    to = [job.owner.email]
    cc = (c.email for c in job.collaborators.all())
    subject = f'Job Run Failed: {job.name}'
    url = settings.ABSOLUTE_URL_BASE + reverse('jobs:detail', args=(job.id,))
    link = f'<a href="{url}">{job.id} ({job.name})</a>'
    body = f'Your job {link} failed. Please visit the link to review failure details and rerun.'
    email = EmailMessage(subject, body, to=to, cc=cc)
    email.content_subtype = "html"
    email.send()

def email_approve_output(job):
    to = [job.owner.email]
    cc = (c.email for c in job.collaborators.all())
    subject = f'Output Approved: {job.name}'
    url = settings.ABSOLUTE_URL_BASE + reverse('jobs:detail', args=(job.id,))
    link = f'<a href="{url}">{job.id} ({job.name})</a>'
    body = f'The output of job {link} was approved and may now be viewed.'
    email = EmailMessage(subject, body, to=to, cc=cc)
    email.content_subtype = "html"
    email.send()

def email_reject_output(job):
    to = [job.owner.email]
    cc = (c.email for c in job.collaborators.all())
    subject = f'Output Rejected: {job.name}'
    url = settings.ABSOLUTE_URL_BASE + reverse('jobs:detail', args=(job.id,))
    link = f'<a href="{url}">{job.id} ({job.name})</a>'
    body = f'The output of job {link} was rejected. Please visit the link to see the next steps and resubmit your job.'
    email = EmailMessage(subject, body, to=to, cc=cc)
    email.content_subtype = "html"
    email.send()

TRANSITION_EMAILS = {
    'approve_code': email_approve_code,
    'reject_code': email_reject_code,
    'complete_job_run': email_complete_job_run,
    'fail_job_run': email_fail_job_run,
    'approve_output': email_approve_output,
    'reject_output': email_reject_output,
}

@receiver(post_transition, sender=Job)
def job_post_transition(sender, **kwargs): # instance, name, source, target
    name = kwargs['name']
    job = kwargs['instance']
    email = TRANSITION_EMAILS.get(name, None)
    if not email:
        return
    email(job)
