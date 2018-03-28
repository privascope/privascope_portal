import enum
import json
import base64

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic.edit import FormView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils.datastructures import MultiValueDictKeyError
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.admin.models import LogEntry
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.conf import settings

from django_fsm import can_proceed
from django_fsm_log.models import StateLog

from .models import Job, Comment
from .forms import JobSubmissionForm


def home(request):
    return render(request, 'jobs/home.html')


@login_required
def index(request):
    jobs = Job.objects.exclude(status=Job.Status.DELETED.name).order_by('-id')
    ctx = {
        'jobs': jobs,
    }
    return render(request, 'jobs/list.html', ctx)


class CreateView(LoginRequiredMixin, FormView):
    template_name = 'jobs/create.html'
    form_class = JobSubmissionForm

    def form_valid(self, form):
        file = form.cleaned_data['file']
        filename = form.cleaned_data['file'].name
        form_collaborators = form.cleaned_data['collaborators']
        collaborators = User.objects.filter(id__in=form_collaborators)
        job = Job.objects.create(
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
                status=Job.Status.PENDING_CODE_REVIEW.name,
                owner=self.request.user,
                filename=filename,
                file=file,
                submitted_at=timezone.now(),
            )
        job.collaborators.set(collaborators)
        self.success_url = reverse('jobs:detail', args=(job.id,))
        return super().form_valid(form)


@login_required
def job_file(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    response = HttpResponse(job.file, content_type='application/tar+gzip')
    response['Content-Disposition'] = f'inline; filename="{job.filename}"'
    return response


@login_required
def job_output(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if (request.user.is_staff or job.status_enum is Job.Status.RELEASED):
        response = HttpResponse(job.output, content_type='application/tar+gzip')
        response['Content-Disposition'] = f'inline; filename="{job.output.name}"'
        return response
    else:
        return HttpResponse(status=401)


@login_required
def job_errors(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if (request.user.is_staff or job.status_enum is Job.Status.RELEASED):
        response = HttpResponse(job.errors, content_type='application/tar+gzip')
        response['Content-Disposition'] = f'inline; filename="{job.errors.name}"'
        return response
    else:
        return HttpResponse(status=401)


@login_required
def logout(request):
    auth_logout(request)
    return HttpResponseRedirect(reverse('jobs:home'))


def generate_status_nodes_widget(current_status, action_required, failed):
    reached_final = False
    displayable = [e for e in Job.Status if not e.value['is_failure']]
    status_nodes = [
        {
            'label': 'Submit',
            'is_failure': False,
            'css_class': 'done'
        }
    ]
    for status in displayable:
        if reached_final:
            status.value['css_class'] = 'unreached'
            status_nodes.append(status.value)
        elif current_status is status:
            reached_final = True
            status.value['css_class'] = 'pending' if not status.value['is_success'] else 'done'
            title = status.value['label']
            status_nodes.append(status.value)
        elif current_status.value['is_failure'] and ((current_status.value['code'] - status.value['code'] < 10) and (current_status.value['code'] - status.value['code'] > 0)) or (current_status.value['code'] == 0):
            reached_final = True
            status.value['css_class'] = 'failed'
            title = current_status.value['label']
            status_nodes.append(status.value)
        else:
            status.value['css_class'] = 'done'
            status_nodes.append(status.value)
    return {
        'title': title, 
        'action_required': action_required, 
        'status_nodes': status_nodes
    }


@login_required
def details(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    try:
        action_required = job.comments.all().latest('id')
    except Comment.DoesNotExist:
        action_required = None
    status_nodes_widget = generate_status_nodes_widget(job.status_enum(), action_required, job.failed)
    ctx = {
        'job': job,
        'status_nodes_widget': status_nodes_widget,
    }
    return render(request, 'jobs/detail.html', ctx)


class EventType(enum.Enum):
    COMMENT = 'Comment'
    FSM = 'State Change'
    ADMIN = 'Edited by Admin'


state_transition_messages = {
    'approve_code': "The job's code has been approved and added to the queue.",
    'reject_code': "The job's code was rejected.",
    'run_job': "The job has started running.",
    'complete_job_run': "The job has successfully finished running.",
    'fail_job_run': "The job failed due to an error.",
    'approve_output': "The job's output was approved and released.",
    'reject_output': "The job's output was rejected.",
}

@login_required
def history(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    def comment_to_event(comment):
        return {
            'type': EventType.COMMENT,
            'timestamp': comment.timestamp,
            'message': comment.text,
            'user': comment.by,
        }
    comments_as_events = list(map(comment_to_event, job.comments.all()))
    def fsm_log_to_event(fsm_log):
        return {
            'type': EventType.FSM,
            'timestamp': fsm_log.timestamp,
            'message': state_transition_messages[fsm_log.transition] if fsm_log.transition in state_transition_messages else fsm_log.transition,
            'user': fsm_log.by,
        }
    fsm_logs = StateLog.objects.for_(job)
    fsm_logs_as_events = list(map(fsm_log_to_event, fsm_logs))
    # Disable admin logs to avoid formatting them
    # def admin_log_to_event(admin_log):
    #     return {
    #         'type': EventType.ADMIN,
    #         'timestamp': admin_log.action_time,
    #         'message': admin_log.change_message,
    #         'user': admin_log.user,
    #     }
    # admin_logs = LogEntry.objects.filter(
    #     object_id = job.id,
    #     content_type = get_content_type_for_model(job)
    # )
    # admin_logs_as_events = list(map(admin_log_to_event, admin_logs))
    events = sorted(comments_as_events + fsm_logs_as_events, key=lambda e: e['timestamp'])
    ctx = {
        'events': events,
    }
    return render(request, 'jobs/history.html', ctx)

@csrf_exempt
def start_job(request):
    if (request.method != 'POST'):
        return HttpResponse(status=404)
    try:
        json_data = json.loads(request.body)
    except Exception as e:
        print(e)
        return HttpResponse('Invalid JSON', status=400)
    correct_key = settings.RUNNER_KEY
    if 'key' not in json_data:
        print('No key!')
        return HttpResponse('Unauthorized', status=401)
    key = json_data['key']
    if (key != correct_key):
        return HttpResponse('Unauthorized', status=401)
    job_id = json_data['id']
    job = get_object_or_404(Job, pk=job_id)
    job.run_job()
    job.save()
    return HttpResponse(status=200)

@csrf_exempt
def complete_job(request):
    if (request.method != 'POST'):
        return HttpResponse(status=404)
    try:
        json_data = json.loads(request.body)
    except Exception as e:
        print(e)
        return HttpResponse('Invalid JSON', status=400)
    correct_key = settings.RUNNER_KEY
    if 'key' not in json_data:
        return HttpResponse('Unauthorized', status=401)
    key = json_data['key']
    if (key != correct_key):
        return HttpResponse('Unauthorized', status=401)
    job_id = json_data['id']
    job = get_object_or_404(Job, pk=job_id)
    output = base64.b64decode(json_data['output']) if 'output' in json_data else None
    errors = base64.b64decode(json_data['errors']) if 'errors' in json_data else None
    job.complete_job_run(output=output, errors=errors)
    job.save()
    return HttpResponse(status=200)
    
@csrf_exempt
def fail_job(request):
    if (request.method != 'POST'):
        return HttpResponse(status=404)
    try:
        json_data = json.loads(request.body)
    except Exception as e:
        print(e)
        return HttpResponse('Invalid JSON', status=400)
    correct_key = settings.RUNNER_KEY
    if 'key' not in json_data:
        return HttpResponse('Unauthorized', status=401)
    key = json_data['key']
    if (key != correct_key):
        return HttpResponse('Unauthorized', status=401)
    job_id = json_data['id']
    job = get_object_or_404(Job, pk=job_id)
    output = base64.b64decode(json_data['output']) if 'output' in json_data else None
    errors = base64.b64decode(json_data['errors']) if 'errors' in json_data else None
    job.fail_job_run(output=output, errors=errors)
    job.save()
    return HttpResponse(status=200)