from django.forms import ModelForm, ValidationError

from .models import Job

class JobSubmissionForm(ModelForm):
    class Meta:
        model = Job
        fields = ['name', 'description', 'file', 'collaborators']

    def clean_file(self):
        import tarfile
        file = self.cleaned_data['file']
        if not tarfile.is_tarfile(file.temporary_file_path()):
            raise ValidationError("File is not a valid tarfile")
        return file
