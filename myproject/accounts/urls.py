from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        next_page='accounts:home'
    ), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(
        template_name='registration/logged_out.html',
        next_page='accounts:home'
    ), name='logout'),
    
    # Main URLs
    path('', views.home, name='home'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('incidents/', views.incident_list, name='incident_list'),
    
    # Admin URLs
    path('admin/incidents/', views.incident_list, name='admin_incident_list'),
    path('admin/incident/<int:id>/', views.admin_incident_detail, name='admin_incident_detail'),
    path('admin/incident/<int:id>/edit/', views.admin_incident_edit, name='admin_incident_edit'),
    path('admin/incident/<int:id>/remarks/', views.admin_dpo_remarks, name='admin_dpo_remarks'),
    path('admin/incident/<int:id>/delete/', views.admin_delete_incident, name='admin_delete_incident'),
    
    # Regular incident URLs
    path('incident/<int:pk>/', views.incident_detail, name='incident_detail'),
    path('incident/<int:pk>/edit/', views.incident_edit, name='incident_edit'),
    path('incident/<int:pk>/delete/', views.incident_delete, name='incident_delete'),
    path('incident/export/', views.incident_export, name='incident_export'),
    path('report-incident/', views.report_incident, name='report_incident'),
    path('generate-summary/', views.generate_summary, name='generate_summary'),
    path('test-auth/', views.test_auth, name='test_auth'),
]



