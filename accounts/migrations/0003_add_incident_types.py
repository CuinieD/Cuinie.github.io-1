from django.db import migrations

def create_incident_types(apps, schema_editor):
    IncidentType = apps.get_model('accounts', 'IncidentType')
    
    incident_types = [
        {'name': 'Data Breach', 'description': 'Unauthorized access or exposure of sensitive data'},
        {'name': 'System Outage', 'description': 'Unexpected system or service downtime'},
        {'name': 'Security Breach', 'description': 'Unauthorized access to systems or networks'},
        {'name': 'Malware Attack', 'description': 'Infection by malicious software'},
        {'name': 'Phishing Attempt', 'description': 'Social engineering attacks via email or messaging'},
        {'name': 'DDoS Attack', 'description': 'Distributed Denial of Service attack'},
        {'name': 'Hardware Failure', 'description': 'Physical equipment malfunction or damage'},
        {'name': 'Software Error', 'description': 'Application or system software malfunction'},
        {'name': 'Others', 'description': 'Other types of incidents not listed above'},
    ]
    
    for type_data in incident_types:
        IncidentType.objects.create(**type_data)

def remove_incident_types(apps, schema_editor):
    IncidentType = apps.get_model('accounts', 'IncidentType')
    IncidentType.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_alter_incident_date_submitted'),
    ]

    operations = [
        migrations.RunPython(create_incident_types, remove_incident_types),
    ]
