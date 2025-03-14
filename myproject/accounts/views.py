from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, FileResponse
from django.template.loader import render_to_string
from .models import Incident, IncidentType
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import datetime, timedelta
import json
import csv
from django.contrib import messages
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from .forms import IncidentForm

def home(request):
    return render(request, 'accounts/home.html')

def home_view(request):
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
def incident_detail(request, id):
    incident = get_object_or_404(Incident, id=id)
    return render(request, 'accounts/admin/incident_detail.html', {'incident': incident})

@login_required
def incident_edit(request, id):
    incident = get_object_or_404(Incident, id=id)
    return render(request, 'accounts/admin/incident_edit.html', {'incident': incident})

@login_required
def incident_delete(request, pk):
    if request.method == 'POST':
        incident = get_object_or_404(Incident, pk=pk)
        incident.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)

@login_required
def incident_export(request):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"incident_report_{timestamp}.csv"
    
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )

    writer = csv.writer(response)
    writer.writerow([
        'Incident ID',
        'Incident Number',
        'Reporter Name',
        'Position',
        'Department',
        'Incident Type',
        'Status',
        'Description',
        'Scope',
        'Systems Affected Count',
        'Data Subjects Count',
        'Impact Level',
        'Discovery Date',
        'Incident Date',
        'Containment Date',
        'DPO Remarks',
        'Last Updated'
    ])

    incidents = Incident.objects.all().order_by('-date_submitted')
    
    for incident in incidents:
        writer.writerow([
            incident.id,
            incident.incident_number,
            incident.reporter_name,
            incident.position,
            incident.department,
            incident.incident_type.name if incident.incident_type else '',
            incident.status,
            incident.description,
            incident.scope,
            incident.systems_affected_count,
            incident.data_subjects_count,
            incident.impact_level,
            incident.discovery_date.strftime('%Y-%m-%d %H:%M:%S') if incident.discovery_date else '',
            incident.incident_date.strftime('%Y-%m-%d %H:%M:%S') if incident.incident_date else '',
            incident.containment_date.strftime('%Y-%m-%d %H:%M:%S') if incident.containment_date else '',
            incident.dpo_remarks,
            incident.last_updated.strftime('%Y-%m-%d %H:%M:%S') if incident.last_updated else ''
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
def dpo_remarks(request, id):
    incident = get_object_or_404(Incident, id=id)
    return render(request, 'accounts/admin/dpo_remarks.html', {'incident': incident})

@login_required
def generate_summary(request):
    # Create response
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    elements.append(Paragraph("Incident Report Summary", title_style))
    elements.append(Spacer(1, 20))

    # Date range
    now = timezone.now()
    date_range = Paragraph(
        f"Report generated on: {now.strftime('%Y-%m-%d %H:%M')}",
        styles['Normal']
    )
    elements.append(date_range)
    elements.append(Spacer(1, 20))

    # Overall Statistics
    total_incidents = Incident.objects.count()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_incidents = Incident.objects.filter(date_submitted__gte=month_start).count()
    week_start = now - timedelta(days=now.weekday())
    weekly_incidents = Incident.objects.filter(date_submitted__gte=week_start).count()

    stats_data = [
        ['Metric', 'Count'],
        ['Total Incidents', str(total_incidents)],
        ['This Month', str(monthly_incidents)],
        ['This Week', str(weekly_incidents)],
    ]

    stats_table = Table(stats_data, colWidths=[300, 100])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))

    # Incident Types Breakdown
    elements.append(Paragraph("Incident Types Breakdown", styles['Heading2']))
    elements.append(Spacer(1, 12))

    incident_types = IncidentType.objects.annotate(count=Count('incident'))
    type_data = [['Incident Type', 'Count', 'Percentage']]
    
    for incident_type in incident_types:
        percentage = (incident_type.count / total_incidents * 100) if total_incidents > 0 else 0
        type_data.append([
            incident_type.name,
            str(incident_type.count),
            f"{percentage:.1f}%"
        ])

    type_table = Table(type_data, colWidths=[200, 100, 100])
    type_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(type_table)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Create the HTTP response
    response = FileResponse(buffer, as_attachment=True, filename='incident_summary.pdf')
    return response

def download_report(request, pk):
    # Fetch the incident by primary key
    incident = get_object_or_404(Incident, pk=pk)
    
    # Create a response object with the appropriate content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="incident_{incident.id}.pdf"'
    
    # Generate the PDF (this is a placeholder, replace with actual PDF generation logic)
    response.write("PDF content goes here")
    
    return response

def delete_incident(request, id):
    incident = get_object_or_404(Incident, id=id)
    if request.method == 'POST':
        incident.delete()
        return redirect('accounts:incident_list')
    return redirect('accounts:incident_list')

@login_required
def admin_incident_detail(request, id):
    incident = get_object_or_404(Incident, id=id)
    if request.method == 'POST':
        form = IncidentForm(request.POST, instance=incident)
        if form.is_valid():
            form.save()
            return redirect('accounts:admin_incident_list')
    else:
        form = IncidentForm(instance=incident)
    
    return render(request, 'accounts/admin/incident_detail.html', {
        'incident': incident,
        'form': form
    })

@login_required
def admin_incident_edit(request, id):
    incident = get_object_or_404(Incident, id=id)
    if request.method == 'POST':
        form = IncidentForm(request.POST, request.FILES, instance=incident)
        if form.is_valid():
            form.save()
            return redirect('accounts:admin_incident_list')
    else:
        form = IncidentForm(instance=incident)
    
    return render(request, 'accounts/admin/incident_edit.html', {
        'incident': incident,
        'form': form,
        'incident_types': IncidentType.objects.all(),
        'status_choices': Incident.STATUS_CHOICES
    })

@login_required
def admin_dpo_remarks(request, id):
    incident = get_object_or_404(Incident, id=id)
    if request.method == 'POST':
        # Update DPO remarks and status
        incident.dpo_remarks = request.POST.get('dpo_remarks')
        incident.dpo_status = request.POST.get('dpo_status')
        incident.dpo_evaluation_date = timezone.now()
        incident.save()
        return redirect('accounts:admin_incident_list')
    
    return render(request, 'accounts/admin/dpo_remarks.html', {
        'incident': incident,
        'dpo_status_choices': Incident.DPO_STATUS_CHOICES
    })

@login_required
def admin_delete_incident(request, id):
    incident = get_object_or_404(Incident, id=id)
    if request.method == 'POST':
        incident.delete()
        return redirect('accounts:admin_incident_list')
    return render(request, 'accounts/admin/incident_delete.html', {'incident': incident})

@login_required
def test_auth(request):
    return render(request, 'accounts/test_auth.html')

