from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm

# Dashboard View
@login_required
def dashboard(request):
    return render(request, 'app/dashboard.html')

# Projects View
@login_required
def projects(request):
    return render(request, 'app/projects.html')

# Tasks View
@login_required
def tasks(request):
    return render(request, 'app/tasks.html')

# Members View
@login_required
def members(request):
    return render(request, 'app/members.html')

# Profile View
@login_required
def profile(request):
    return render(request, 'app/dashboard.html')

# Register View
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'app/register.html', {'form': form})
