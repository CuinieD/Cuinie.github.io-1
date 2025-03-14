from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class IncidentType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Incident(models.Model):
    IMPACT_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ]

    DPO_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('needs_action', 'Needs Action'),
        ('rejected', 'Rejected')
    ]

    # Incident Identification
    incident_number = models.CharField(max_length=50, unique=True)
    year = models.IntegerField(default=timezone.now().year)
    date_submitted = models.DateTimeField(auto_now_add=True)
    reporter_name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100)

    # Incident Details
    incident_type = models.ForeignKey('IncidentType', on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(verbose_name='Description of Incident', default='Not provided')
    scope = models.TextField(verbose_name='Scope of Incident', default='Not provided')
    systems_affected_count = models.IntegerField(verbose_name='Estimated Quantity of Systems Affected')
    data_subjects_count = models.IntegerField(verbose_name='Estimated Quantity of Data Subjects Affected')
    data_subjects_groups = models.TextField(verbose_name='Data Subjects Affected', default='Not provided')
    additional_scope_info = models.TextField(verbose_name='Additional Scope Information', blank=True, null=True)

    # Impact Assessment
    impact_level = models.CharField(max_length=20, choices=IMPACT_CHOICES, verbose_name='Impact of Incident')
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Estimated Total Cost Incurred', null=True, blank=True)
    additional_impact_info = models.TextField(verbose_name='Additional Impact Information', blank=True, null=True)
    data_sensitivity = models.TextField(verbose_name='Sensitivity of Affected Data/Information', default='Not provided')
    data_quantity = models.TextField(verbose_name='Quantity of Data/Information Affected', default='Not provided')
    additional_data_info = models.TextField(verbose_name='Additional Affected Data Information', blank=True, null=True)

    # Technical Details
    attack_sources = models.TextField(verbose_name='Attack Sources', default='Not specified')
    attack_destinations = models.TextField(verbose_name='Attack Destinations', default='Not specified')
    affected_ips = models.TextField(verbose_name='IP Addresses of Affected Systems', default='Not specified')
    affected_domains = models.TextField(verbose_name='Domain Names of Affected Systems', default='Not specified')
    system_functions = models.TextField(verbose_name='Primary Functions of Affected Systems', default='Not specified')
    operating_systems = models.TextField(verbose_name='Operating Systems of Affected Systems', default='Not specified')
    patch_levels = models.TextField(verbose_name='Patch Level of Affected Systems', default='Not specified')
    security_software = models.TextField(verbose_name='Security Software Loaded on Affected Systems', default='Not specified')
    physical_location = models.TextField(verbose_name='Physical Location of Affected Systems', default='Not specified')
    additional_system_details = models.TextField(verbose_name='Additional System Details', blank=True, null=True)

    # User Details
    affected_user_titles = models.TextField(verbose_name='Job Titles of Affected Users', default='Not specified')
    access_levels = models.TextField(verbose_name='System Access Levels or Rights of Affected Users', default='Not specified')
    additional_user_details = models.TextField(verbose_name='Additional User Details', blank=True, null=True)

    # Incident Timeline
    discovery_date = models.DateTimeField(verbose_name='Date and Time of Discovery')
    incident_date = models.DateTimeField(verbose_name='Date and Time When the Actual Incident Occurred')
    containment_date = models.DateTimeField(verbose_name='Date and Time When the Incident Was Contained', null=True, blank=True)
    detailed_timeline = models.TextField(verbose_name='Detailed Incident Timeline', default='Not provided')

    # Attachments
    attachments = models.FileField(upload_to='incident_attachments/', verbose_name='Supporting Documents', null=True, blank=True)
    attachment = models.FileField(upload_to='incident_attachments/', null=True, blank=True, verbose_name='Attachment')

    # Last updated timestamp
    last_updated = models.DateTimeField(auto_now=True)

    # Actions Taken Fields
    actions_identify_resources = models.TextField(blank=True, null=True)
    actions_address_incident = models.TextField(blank=True, null=True)
    actions_mitigate_harm = models.TextField(blank=True, null=True)
    actions_prevent_similar = models.TextField(blank=True, null=True)
    additional_actions_planned = models.TextField(blank=True, null=True)
    
    # DPO Evaluation Fields
    dpo_remarks = models.TextField(blank=True, null=True)
    dpo_evaluation_date = models.DateTimeField(blank=True, null=True)
    dpo_status = models.CharField(max_length=20, choices=DPO_STATUS_CHOICES, default='pending')

    @property
    def elapsed_time_to_discovery(self):
        """Calculate time between incident and discovery"""
        if self.incident_date and self.discovery_date:
            elapsed = self.discovery_date - self.incident_date
            days = elapsed.days
            hours = elapsed.seconds // 3600
            minutes = (elapsed.seconds % 3600) // 60
            return f"{days} days, {hours} hours, {minutes} minutes"
        return "Not available"

    @property
    def elapsed_time_to_restoration(self):
        """Calculate time between discovery and containment"""
        if self.discovery_date and self.containment_date:
            elapsed = self.containment_date - self.discovery_date
            days = elapsed.days
            hours = elapsed.seconds // 3600
            minutes = (elapsed.seconds % 3600) // 60
            return f"{days} days, {hours} hours, {minutes} minutes"
        return "Not available"

    def save(self, *args, **kwargs):
        if not self.incident_number:
            current_time = timezone.localtime(timezone.now())
            self.year = current_time.year
            count = Incident.objects.filter(date_submitted__year=self.year).count() + 1
            self.incident_number = f'IR-{self.year}-{count:04d}'
        
        # Update incident status based on DPO status
        if self.dpo_status == 'approved':
            self.status = 'resolved'
        elif self.dpo_status == 'needs_action':
            self.status = 'in_progress'
        elif self.dpo_status == 'rejected':
            self.status = 'in_progress'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.incident_number

    class Meta:
        ordering = ['-date_submitted']

