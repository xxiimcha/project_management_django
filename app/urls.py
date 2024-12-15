from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Dashboard URL
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Projects Page
    path('projects/', views.projects, name='projects'),
    path('projects/create/', views.projects, name='create_project'),
    path('projects/details/<int:project_id>/', views.project_details, name='project_details'),

    # Tasks Page
    path('tasks/', views.tasks, name='tasks'),

    # Members Page
    path('members/', views.members, name='members'),

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
