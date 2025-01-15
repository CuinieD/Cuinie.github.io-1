from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('incidents/', views.incident_list, name='incident_list'),
    path('incident/<int:pk>/', views.incident_detail, name='incident_detail'),
    path('incident/<int:pk>/edit/', views.incident_edit, name='incident_edit'),
    path('incident/<int:pk>/delete/', views.incident_delete, name='incident_delete'),
    path('incident/export/', views.incident_export, name='incident_export'),
    path('report-incident/', views.report_incident, name='report_incident'),
    path('incident-list/', views.incident_list, name='incident_list'),
    path('incident/<int:pk>/dpo-remarks/', views.dpo_remarks, name='dpo_remarks'),
]



