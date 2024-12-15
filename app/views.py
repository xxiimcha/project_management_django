from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User  # Import User model
from django.contrib import messages
from .models import TeamMember
from .project_crud import get_projects, create_project
from .forms import RegisterForm

# Dashboard View
@login_required
def dashboard(request):
    return render(request, 'app/dashboard.html')

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
@login_required
def profile(request):
    return render(request, 'app/profile.html')

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
