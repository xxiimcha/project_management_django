from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User  # Import User model
from django.contrib import messages
from .models import TeamMember, Task
from .project_crud import get_projects, create_project
from .forms import RegisterForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Q, F

# Dashboard View
@login_required
def dashboard(request):
    # Task counts based on status
    task_counts = {
        'not_started': Task.objects.filter(status='not-started').count(),
        'in_progress': Task.objects.filter(status='in-progress').count(),
        'done': Task.objects.filter(status='done').count(),
        'urgent': Task.objects.filter(status='urgent').count(),
    }

    # Team member progress table
    team_progress = (
        Task.objects.filter(status='done')
        .values(assignee_name=F('assignee__first_name'), assignee_id=F('assignee__id'))
        .annotate(
            total_tasks=Count('id'),
            on_time=Count('id', filter=Q(due_date__gte=F('date_created'))),
            delayed=Count('id', filter=Q(due_date__lt=F('date_created'))),
        )
    )

    # Project timeline Gantt data
    project_tasks = Task.objects.select_related('project').order_by('due_date')

    context = {
        'task_counts': task_counts,
        'team_progress': team_progress,
        'project_tasks': project_tasks,
    }

    return render(request, 'app/dashboard.html', context)

# Projects View
@login_required
def projects(request):
    try:
        if request.method == "POST":
            # Call the create_project function
            create_project(request.POST, request.user)
            messages.success(request, "Project created successfully!")
            return redirect('projects')

        # Fetch team members for the dropdown
        team_members = TeamMember.objects.all()
        return render(request, 'app/projects.html', {'team_members': team_members})

    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        return redirect('dashboard')

# Tasks View
@login_required
def tasks(request):
    return render(request, 'app/tasks.html')

# Members View
@login_required
def members(request):
    try:
        if request.method == "POST":
            # Extract form data
            name = request.POST.get('name')
            email = request.POST.get('email')

            # Default password for new members
            default_password = "defaultpassword123"

            # Validate if user exists
            if User.objects.filter(email=email).exists():
                messages.error(request, "A user with this email already exists.")
            else:
                # Split name into first and last
                first_name, *last_name = name.split()
                last_name = " ".join(last_name) if last_name else ""

                # Create user
                new_user = User.objects.create_user(
                    username=email.split('@')[0],
                    email=email,
                    password=default_password,
                    first_name=first_name,
                    last_name=last_name
                )

                # Create team member
                TeamMember.objects.create(
                    user=new_user,
                    added_by=request.user
                )
                messages.success(request, "Member added successfully!")

            return redirect('members')

        # Fetch all team members
        team_members = TeamMember.objects.all()
        return render(request, 'app/members.html', {'team_members': team_members})

    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        return redirect('dashboard')

# Profile View
def profile(request):
    return render(request, 'app/profile.html')

@login_required
def edit_profile(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST['first_name']
        user.last_name = request.POST['last_name']
        user.email = request.POST['email']
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')

@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            messages.success(request, "Password changed successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'app/profile.html', {'form': form})

@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        user.delete()
        messages.success(request, "Your account has been deleted.")
        return redirect('login')
    
# Register View
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect('login')
        else:
            messages.error(request, "There was an error during registration. Please check the form.")
    else:
        form = RegisterForm()
    return render(request, 'app/register.html', {'form': form})
