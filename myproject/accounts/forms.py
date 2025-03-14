from django import forms
from .models import Incident

class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            'incident_number',
            'reporter_name',
            'position',
            'department',
            'incident_type',
            'status',
            'description',
            'scope',
            'systems_affected_count',
            'data_subjects_count',
            'data_subjects_groups',
            'discovery_date',
            'incident_date',
            'containment_date',
            'detailed_timeline',
            'data_sensitivity',
            'access_levels',
            'affected_user_titles',
            'dpo_remarks',
            'dpo_status'
        ]
        widgets = {
            'discovery_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'incident_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'containment_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'scope': forms.Textarea(attrs={'rows': 4}),
            'detailed_timeline': forms.Textarea(attrs={'rows': 4}),
            'dpo_remarks': forms.Textarea(attrs={'rows': 4}),
        } 