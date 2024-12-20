from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User  # Import User model
from django.contrib import messages
from .models import TeamMember, Task, UserProfile, Project, Notification
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
from django.http import HttpResponse
from django.utils.timezone import now
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth import logout
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, SimpleDocTemplate

@login_required
def logout_view(request):
    """
    Logs out the user and redirects to the login page.
    """
    logout(request)
    return redirect('login')  # Ensure 'login' is the name of your login URL

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

@login_required
def generate_report(request):
    """
    Generate and download a PDF report with project and task details.
    """
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="project_report.pdf"'

    # Initialize document
    doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title = Paragraph("<b><font size=18>Project and Task Report</font></b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 20))  # Add some space

    # Task Status Overview Section
    task_counts = {
        "Not Started": Task.objects.filter(status='not-started').count(),
        "In Progress": Task.objects.filter(status='in-progress').count(),
        "Done": Task.objects.filter(status='done').count(),
        "Urgent": Task.objects.filter(status='urgent').count(),
    }
    task_data = [["<b>Status</b>", "<b>Count</b>"]]
    for status, count in task_counts.items():
        task_data.append([status, count])

    task_table = Table(task_data, colWidths=[200, 100])
    task_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(Paragraph("<b><font size=14>Task Status Overview</font></b>", styles['Heading2']))
    elements.append(Spacer(1, 10))
    elements.append(task_table)
    elements.append(Spacer(1, 20))

    # Projects and Tasks Section
    elements.append(Paragraph("<b><font size=14>Projects and Tasks</font></b>", styles['Heading2']))
    elements.append(Spacer(1, 10))

    projects = Project.objects.prefetch_related('tasks').all()
    for project in projects:
        # Project Title
        project_title = Paragraph(f"<b>Project:</b> {project.name}", styles['Heading3'])
        elements.append(project_title)
        elements.append(Spacer(1, 5))

        # Task Table for Project
        task_data = [["<b>Task Title</b>", "<b>Status</b>", "<b>Priority</b>", "<b>Due Date</b>"]]
        for task in project.tasks.all():
            task_data.append([task.title, task.status.capitalize(), task.priority.capitalize(), task.due_date.strftime('%Y-%m-%d')])

        if len(task_data) > 1:  # Only render if tasks exist
            task_table = Table(task_data, colWidths=[180, 80, 80, 100])
            task_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.aliceblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            elements.append(task_table)
        else:
            elements.append(Paragraph("<i>No tasks available for this project.</i>", styles['BodyText']))

        elements.append(Spacer(1, 20))

    # Build the document
    doc.build(elements)
    return response

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
def delete_project(request, project_id):
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id, created_by=request.user)
        project.delete()
        return JsonResponse({"success": "Project deleted successfully!"})
    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def edit_project(request, project_id):
    """
    View to fetch project details for editing or update project.
    """
    if request.method == "GET" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Fetch project details for AJAX
        project = get_object_or_404(Project, id=project_id, created_by=request.user)
        team_members = project.team_members.values_list('id', flat=True)  # Fetch team member IDs

        data = {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'start_date': str(project.start_date),
            'deadline': str(project.deadline),
            'team_members': list(team_members),
        }
        return JsonResponse(data)
    
    elif request.method == "POST":
        # Handle project update
        project = get_object_or_404(Project, id=project_id, created_by=request.user)
        project.name = request.POST.get('name')
        project.description = request.POST.get('description')
        project.start_date = request.POST.get('start_date')
        project.deadline = request.POST.get('deadline')
        team_members = request.POST.getlist('team_members')  # List of selected team members

        # Update team members (assuming ManyToMany relationship)
        project.team_members.set(team_members)
        project.save()
        
        return JsonResponse({'message': 'Project updated successfully!'})

    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def project_details(request, project_id):
    """
    View to return project details along with its tasks.
    This will render content dynamically for the modal via AJAX.
    """
    # Check if the request is AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            # Fetch the project for the logged-in user
            project = get_object_or_404(Project, id=project_id, created_by=request.user)
            tasks = project.tasks.all()  # Assuming related_name="tasks" on Task model

            # Render the partial HTML for modal content
            return render(request, 'app/modals/_project_details_modal.html', {
                'project': project,
                'tasks': tasks
            })
        except Exception as e:
            # Return a JSON error response in case of any exceptions
            return JsonResponse({'error': str(e)}, status=500)
    else:
        # If not an AJAX request, return a bad request response
        return HttpResponseBadRequest("Invalid request")

    
# Tasks View
@login_required
def tasks(request):
    return render(request, 'app/tasks.html')

from .models import Notification  # Import Notification model

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
            task = Task.objects.create(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                project=project,
                assignee=assignee,
                created_by=request.user
            )

            # Send notification to the assignee
            if assignee:
                Notification.objects.create(
                    user=assignee,
                    message=f"You have been assigned a new task: '{task.title}' in project '{project.name}'."
                )
                messages.success(request, f"Task added and notification sent to {assignee.get_full_name()}!")

            else:
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
from .models import TeamMember, UserProfile  # Ensure UserProfile is imported

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

                # Add role as 'team_member' in UserProfile table
                UserProfile.objects.create(
                    user=new_user,
                    role="team_member"
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

    except Exception as e:
        messages.error(request, f"An error occurred: {e}")
        return redirect('dashboard')


@login_required
def delete_member(request, member_id):
    """
    Deletes a team member by ID.
    """
    if request.method == "POST":
        try:
            member = get_object_or_404(TeamMember, id=member_id, added_by=request.user)
            member_name = member.user.get_full_name()
            member.delete()
            return JsonResponse({"success": f"{member_name} has been deleted."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)

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

# Fetch notifications for team members only
@login_required
def notifications_view(request):
    """
    Display all notifications for team members.
    """
    if request.user.user_profile.role == "team_member":
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'app/notifications.html', {'notifications': notifications})
    return JsonResponse({"error": "Access denied."}, status=403)


# Mark a specific notification as read
@login_required
def mark_notification_read(request, notification_id):
    if request.method == "POST":
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({"message": "Notification marked as read."})
    return JsonResponse({"error": "Invalid request method"}, status=400)


# Mark all notifications as read
@login_required
def mark_all_notifications_read(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({"message": "All notifications marked as read."})
    return JsonResponse({"error": "Invalid request method"}, status=400)


@login_required
def fetch_notifications(request):
    """
    Return JSON response of unread notifications for team members via AJAX.
    """
    try:
        if request.user.profile.role == "team_member":  # Access via 'profile' related_name
            notifications = Notification.objects.filter(user=request.user, is_read=False).values(
                'id', 'message', 'created_at'
            )
            return JsonResponse(list(notifications), safe=False)
        else:
            return JsonResponse({"error": "Access denied. Only team members can view notifications."}, status=403)
    except UserProfile.DoesNotExist:
        return JsonResponse({"error": "UserProfile does not exist for this user."}, status=500)
