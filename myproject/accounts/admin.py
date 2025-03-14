from django.contrib import admin
from .models import Incident, IncidentType

@admin.register(IncidentType)
class IncidentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = (
        'incident_number',
        'get_incident_type',
        'date_submitted',
        'impact_level',
        'reporter_name',
        'department'
    )
    list_filter = (
        'status',
        'impact_level',
        'incident_type',
        'date_submitted',
        'department'
    )
    search_fields = (
        'incident_number',
        'description',
        'department',
        'position',
        'reporter_name'
    )
    date_hierarchy = 'date_submitted'
    readonly_fields = ('incident_number', 'date_submitted', 'last_updated')

    @admin.display(ordering='incident_type__name', description='Type')
    def get_incident_type(self, obj):
        return obj.incident_type.name if obj.incident_type else "-"
