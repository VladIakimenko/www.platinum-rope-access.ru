from django.forms import ModelForm

from reports.models import JobRecord


class JobRecordForm(ModelForm):

    class Meta:
        model = JobRecord
        fields = ['report', 'job_description', 'date']
