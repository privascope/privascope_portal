import time

from django.conf import settings

from rest_framework.response import Response
from rest_framework.decorators import api_view

from .celery import run_job


@api_view(['POST'])
def enqueue(request):
    key = request.data['key']
    if (key != settings.RUNNER_KEY):
        return Response('Unauthorized', status=401)
    id = request.data['id']
    file = request.data['file'] # assume .tar.gz
    owner = request.data['owner']
    run_job.apply_async(countdown=10, args=[{
            'id': id,
            'file': file,
            'owner': owner,
        }]) # Get rid of key so it can't leak
    return Response({'result': 'queued'})
