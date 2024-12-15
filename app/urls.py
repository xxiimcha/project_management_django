from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Dashboard URL
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Projects Page
    path('projects/', views.projects, name='projects'),

    # Tasks Page
    path('tasks/', views.tasks, name='tasks'),

    # Members Page
    path('members/', views.members, name='members'),

    # Profile Page
    path('profile/', views.profile, name='profile'),

    # Logout
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Login and Register
    path('login/', auth_views.LoginView.as_view(template_name='app/login.html'), name='login'),
    path('register/', views.register, name='register'),
]
