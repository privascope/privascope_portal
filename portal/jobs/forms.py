from django.forms import ModelForm

from .models import Job

class JobSubmissionForm(ModelForm):
    class Meta:
        model = Job
        fields = ['name', 'description', 'file', 'collaborators']
