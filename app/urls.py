from django.urls import path
from . import views
from .views import project_details
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Dashboard URL
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('gantt-chart/', views.gantt_chart_view, name='gantt_chart_view'),
    
    # Projects Page
    path('projects/', views.projects, name='projects'),
    path('projects/create/', views.projects, name='create_project'),
    path('projects/details/<int:project_id>/', project_details, name='project_details'),

    # Tasks Page
    path('tasks/', views.tasks_view, name='tasks'),  # Add the tasks page
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/update_status/<int:task_id>/', views.update_task_status, name='update_task_status'),
    path('tasks/update/<int:task_id>/', views.get_task_details, name='get_task_details'),

    # Members Page
    path('members/', views.members, name='members'),
    path('members/delete/<int:member_id>/', views.delete_member, name="delete_member"),

    # Profile Page
    path('accounts/profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/delete/', views.delete_account, name='delete_account'),

    # Logout
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Login and Register
    path('', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.register, name='register'),
]
