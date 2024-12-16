from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User  # Import User model
from django.contrib import messages
from .models import TeamMember, Task, UserProfile, Project
from .project_crud import get_projects, create_project
from .forms import RegisterForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Q, F
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
import json

class CustomLoginView(LoginView):
    template_name = 'app/login.html'

    def form_valid(self, form):
        # Call the parent method to log the user in
        response = super().form_valid(form)

        # Fetch the logged-in user
        user = self.request.user
        print(f"User '{user.username}' (ID: {user.id}) logged in.")  # Log username and user ID

        # Check if the user has a UserProfile, else create one
        user_profile, created = UserProfile.objects.get_or_create(user=user, defaults={'role': 'project_manager'})
        
        # Log the role status
        if created:
            print(f"UserProfile created for '{user.username}' (ID: {user.id}) with default role 'project_manager'.")
        else:
            print(f"UserProfile already exists for '{user.username}' (ID: {user.id}). Role: {user_profile.role}")
        
        # Store the role in the session
        self.request.session['user_role'] = user_profile.role
        messages.success(self.request, f"Welcome back, {user.username}! Role: {user_profile.role}")

        # Redirect to the dashboard
        print(f"Redirecting '{user.username}' (ID: {user.id}) to dashboard.")
        return response
    
# Dashboard View

@login_required
def dashboard(request):
    user = request.user

    # Task counts based on status for tasks created by the logged-in user
    task_counts = {
        'not_started': Task.objects.filter(status='not-started', project__created_by=user).count(),
        'in_progress': Task.objects.filter(status='in-progress', project__created_by=user).count(),
        'done': Task.objects.filter(status='done', project__created_by=user).count(),
        'urgent': Task.objects.filter(status='urgent', project__created_by=user).count(),
    }

    # Team member progress table for tasks created by the logged-in user
    team_progress = (
        Task.objects.filter(status='done', project__created_by=user)
        .values('assignee__first_name', 'assignee__last_name')
        .annotate(
            tasks_completed=Count('id'),
            tasks_on_time=Count('id', filter=Q(due_date__gte=F('date_created'))),
            tasks_delayed=Count('id', filter=Q(due_date__lt=F('date_created'))),
        )
    )

    # Project timeline Gantt data filtered by the logged-in user
    project_tasks = Task.objects.filter(project__created_by=user).select_related('project').order_by('due_date')
    projects = Project.objects.prefetch_related('tasks').filter(created_by=user)

    context = {
        'task_counts': task_counts,
        'team_progress': team_progress,
        'project_tasks': project_tasks,
        'projects': projects,
    }

    return render(request, 'app/dashboard.html', context)


def gantt_chart_view(request):
    projects = Project.objects.prefetch_related('tasks').all()
    return render(request, 'app/gantt_chart.html', {'projects': projects})

# Projects View
@login_required
def projects(request):
    try:
        if request.method == "POST":
            # Call the create_project function
            create_project(request.POST, request.user)
            messages.success(request, "Project created successfully!")
            return redirect('projects')

        # Fetch team members created by the logged-in user
        team_members = TeamMember.objects.filter(added_by_id=request.user)
        
        # Fetch all projects created by the logged-in user
        all_projects = get_projects().filter(created_by=request.user)

        return render(request, 'app/projects.html', {
            'team_members': team_members,
            'all_projects': all_projects
        })

    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        return redirect('dashboard')

@login_required
def project_details(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    tasks = project.tasks.all()  # Assuming related_name="tasks" on Task model
    return render(request, 'app/modals/_project_details_modal.html', {
        'project': project,
        'tasks': tasks
    })

# Tasks View
@login_required
def tasks(request):
    return render(request, 'app/tasks.html')

@login_required
def create_task(request):
    if request.method == "POST":
        title = request.POST['title']
        description = request.POST['description']
        due_date = request.POST['due_date']
        priority = request.POST['priority']
        project_id = request.POST['project_id']
        assignee_id = request.POST.get('assignee_id')  # Optional assignee

        try:
            # Fetch project and assignee if available
            project = Project.objects.get(id=project_id)
            assignee = User.objects.get(id=assignee_id) if assignee_id else None

            # Create Task with created_by set to the current user
            Task.objects.create(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                project=project,
                assignee=assignee,
                created_by=request.user  # Set the creator to the logged-in user
            )
            messages.success(request, "Task added successfully!")
            return redirect('projects')  # Redirect to projects page

        except Project.DoesNotExist:
            messages.error(request, "Project not found!")
        except User.DoesNotExist:
            messages.error(request, "Assignee not found!")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

    # If GET request or error, reload the form
    return render(request, 'app/tasks.html')

    
@login_required
def tasks_view(request):
    """ Render the tasks page with filtered tasks. """
    user_id = request.user.id  # Current logged-in user ID

    # Fetch tasks assigned to the current user
    my_tasks = Task.objects.filter(assignee_id=user_id)
    
    # Optionally, you can filter `all_tasks` to exclude those assigned to the current user
    all_tasks = Task.objects.exclude(assignee_id=user_id)

    context = {
        'all_tasks': all_tasks,
        'my_tasks': my_tasks,
    }
    return render(request, 'app/tasks.html', context)

def get_task_details(request, task_id):
    task = Task.objects.get(id=task_id)
    team_members = User.objects.all()  # Fetch all users to populate the dropdown

    data = {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "due_date": task.due_date.strftime('%Y-%m-%d'),
        "priority": task.priority,
        "assignee_id": task.assignee.id if task.assignee else None,
        "team_members": [
            {"id": member.id, "name": member.get_full_name()} 
            for member in team_members
        ]
    }
    return JsonResponse(data)

@login_required
def update_task_status(request, task_id):
    if request.method == 'POST':
        try:
            # Parse the JSON request body
            data = json.loads(request.body)

            # Retrieve task
            task = Task.objects.get(id=task_id)

            # Update task fields
            task.title = data.get('title', task.title)
            task.status = data.get('status', task.status)
            task.due_date = data.get('due_date', task.due_date)
            task.priority = data.get('priority', task.priority)

            # Update assignee
            assignee_id = data.get('assignee_id')
            if assignee_id:
                task.assignee_id = assignee_id

            task.save()

            return JsonResponse({'success': True, 'status': task.status})
        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

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
        team_members = TeamMember.objects.filter(added_by_id=request.user)
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
            # Save the user instance
            user = form.save()

            # Assign the 'project_manager' role automatically
            UserProfile.objects.create(user=user, role='project_manager')

            messages.success(request, "Registration successful. You have been assigned as a Project Manager. Please log in.")
            return redirect('login')
        else:
            messages.error(request, "There was an error during registration. Please check the form.")
    else:
        form = RegisterForm()
    return render(request, 'app/register.html', {'form': form})