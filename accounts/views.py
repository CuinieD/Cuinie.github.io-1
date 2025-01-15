from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from .models import Incident, IncidentType
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import datetime, timedelta
import json
import csv
from django.contrib import messages

def home_view(request):
    """Home page view"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    return render(request, 'accounts/home.html')

@login_required
def admin_dashboard(request):
    # Get your data
    incidents = Incident.objects.all().order_by('-date_submitted')
    
    # Get current date and time
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    # Monthly Trend data - get last 12 months
    last_12_months = now - timedelta(days=365)
    monthly_incidents = (
        Incident.objects.filter(date_submitted__gte=last_12_months)
        .annotate(month=TruncMonth('date_submitted'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    # Incident Types data
    incident_types = (
        IncidentType.objects.annotate(count=Count('incident'))
        .values('name', 'count')
        .order_by('-count')
    )

    context = {
        'incident_count': incidents.count(),
        'month_count': incidents.filter(date_submitted__gte=month_start).count(),
        'week_count': incidents.filter(date_submitted__gte=week_start).count(),
        'today_count': incidents.filter(date_submitted__gte=today_start).count(),
        'monthly_incidents': json.dumps(list(monthly_incidents), cls=DjangoJSONEncoder),
        'incident_types': json.dumps(list(incident_types), cls=DjangoJSONEncoder),
    }
    
    return render(request, 'accounts/admin/dashboard.html', context)

@login_required
def incident_list(request):
    incidents = Incident.objects.all().order_by('-id')
    return render(request, 'accounts/admin/incident_list.html', {'incidents': incidents})

@login_required
def incident_detail(request, pk):
    incident = get_object_or_404(Incident, pk=pk)
    return render(request, 'accounts/admin/incident_detail.html', {'incident': incident})

@login_required
def incident_edit(request, pk):
    incident = get_object_or_404(Incident, pk=pk)
    incident_types = IncidentType.objects.all()

    if request.method == 'POST':
        try:
            # Update incident fields
            incident.reporter_name = request.POST.get('reporter_name')
            incident.department = request.POST.get('department')
            incident.position = request.POST.get('position')
            incident.incident_type_id = request.POST.get('incident_type')
            incident.status = request.POST.get('status')
            incident.description = request.POST.get('description')
            incident.scope = request.POST.get('scope')
            incident.systems_affected_count = request.POST.get('systems_affected_count', 0)
            incident.data_subjects_count = request.POST.get('data_subjects_count', 0)
            
            # Handle dates
            if request.POST.get('discovery_date'):
                incident.discovery_date = timezone.make_aware(datetime.strptime(request.POST.get('discovery_date'), '%Y-%m-%dT%H:%M'))
            if request.POST.get('incident_date'):
                incident.incident_date = timezone.make_aware(datetime.strptime(request.POST.get('incident_date'), '%Y-%m-%dT%H:%M'))
            if request.POST.get('containment_date'):
                incident.containment_date = timezone.make_aware(datetime.strptime(request.POST.get('containment_date'), '%Y-%m-%dT%H:%M'))
            
            # Handle attachment
            if 'delete_attachment' in request.POST:
                if incident.attachment:
                    incident.attachment.delete()
                    incident.attachment = None
            
            if 'attachment' in request.FILES:
                if incident.attachment:
                    incident.attachment.delete()
                incident.attachment = request.FILES['attachment']

            incident.save()
            return redirect('incident_list')
        except Exception as e:
            messages.error(request, f'Error updating incident: {str(e)}')
    
    context = {
        'incident': incident,
        'incident_types': incident_types,
        'status_choices': Incident.STATUS_CHOICES,
    }
    return render(request, 'accounts/admin/incident_edit.html', context)

@login_required
def incident_delete(request, pk):
    if request.method == 'POST':
        incident = get_object_or_404(Incident, pk=pk)
        incident.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)

@login_required
def incident_export(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="incidents.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Incident Number',
        'Date Submitted',
        'Reporter Name',
        'Department',
        'Position',
        'Incident Type',
        'Status',
        'Description',
        'Scope',
        'Systems Affected',
        'Data Subjects Affected',
        'Discovery Date',
        'Incident Date',
        'Containment Date',
        'Time to Discovery',
        'Time to Restoration'
    ])
    
    incidents = Incident.objects.all().order_by('-date_submitted')
    for incident in incidents:
        writer.writerow([
            incident.incident_number,
            incident.date_submitted.strftime('%Y-%m-%d %H:%M:%S'),
            incident.reporter_name,
            incident.department,
            incident.position,
            incident.incident_type.name if incident.incident_type else 'N/A',
            dict(Incident.STATUS_CHOICES)[incident.status],
            incident.description,
            incident.scope,
            incident.systems_affected_count,
            incident.data_subjects_count,
            incident.discovery_date.strftime('%Y-%m-%d %H:%M:%S') if incident.discovery_date else 'N/A',
            incident.incident_date.strftime('%Y-%m-%d %H:%M:%S') if incident.incident_date else 'N/A',
            incident.containment_date.strftime('%Y-%m-%d %H:%M:%S') if incident.containment_date else 'N/A',
            incident.elapsed_time_to_discovery,
            incident.elapsed_time_to_restoration
        ])
    
    return response

def report_incident(request):
    if request.method == 'POST':
        try:
            incident_type = request.POST.get('incident_type')
            other_type = request.POST.get('other_incident_type')
            
            # If "Others" is selected, create a new incident type
            if incident_type == 'others' and other_type:
                new_type = IncidentType.objects.create(
                    name=other_type,
                    description=f'User specified incident type: {other_type}'
                )
                incident_type_id = new_type.id
            else:
                incident_type_id = incident_type
            
            # Create new incident
            incident = Incident(
                reporter_name=request.POST.get('reporter_name'),
                position=request.POST.get('position'),
                department=request.POST.get('department'),
                incident_type_id=incident_type_id,
                description=request.POST.get('description'),
                scope=request.POST.get('scope'),
                systems_affected_count=request.POST.get('systems_affected_count', 0),
                data_subjects_count=request.POST.get('data_subjects_count', 0),
                data_subjects_groups=request.POST.get('data_subjects_groups'),
                discovery_date=timezone.make_aware(datetime.strptime(request.POST.get('discovery_date'), '%Y-%m-%dT%H:%M')),
                incident_date=timezone.make_aware(datetime.strptime(request.POST.get('incident_date'), '%Y-%m-%dT%H:%M')),
                containment_date=timezone.make_aware(datetime.strptime(request.POST.get('containment_date'), '%Y-%m-%dT%H:%M')) if request.POST.get('containment_date') else None,
                detailed_timeline=request.POST.get('detailed_timeline'),
                data_sensitivity=request.POST.get('data_sensitivity'),
                access_levels=request.POST.get('access_levels'),
                affected_user_titles=request.POST.get('affected_user_titles'),
                status='new'
            )
            incident.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Incident report submitted successfully.'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    # For GET requests
    context = {
        'incident_types': IncidentType.objects.all().order_by('name'),
        'incident_number': f'IR-{timezone.now().year}-{Incident.objects.count() + 1:04d}',
        'current_year': timezone.now().year,
    }
    return render(request, 'accounts/report_incident.html', context)

from django import template
from django.core.serializers.json import DjangoJSONEncoder
import json

register = template.Library()

@login_required
def dpo_remarks(request, pk):
    incident = get_object_or_404(Incident, pk=pk)
    
    if request.method == 'POST':
        # Update actions taken
        incident.actions_identify_resources = request.POST.get('actions_identify_resources')
        incident.actions_address_incident = request.POST.get('actions_address_incident')
        incident.actions_mitigate_harm = request.POST.get('actions_mitigate_harm')
        incident.actions_prevent_similar = request.POST.get('actions_prevent_similar')
        incident.additional_actions_planned = request.POST.get('additional_actions_planned')
        
        # Update DPO evaluation
        incident.dpo_remarks = request.POST.get('dpo_remarks')
        incident.dpo_status = request.POST.get('dpo_status')
        incident.dpo_evaluation_date = timezone.now()
        
        incident.save()
        messages.success(request, 'DPO evaluation updated successfully.')
        return redirect('incident_list')
    
    return render(request, 'accounts/admin/dpo_remarks.html', {'incident': incident})

