from .models import Task, Project
from django.contrib.auth.models import User

def create_task(data):
    """Create a new task."""
    project = Project.objects.get(id=data['project'])
    assignee = User.objects.get(id=data['assignee'])
    task = Task.objects.create(
        title=data['title'],
        description=data['description'],
        start_date=data['start_date'],
        deadline=data['deadline'],
        status=data['status'],
        project=project,
        assignee=assignee
    )
    return task

def get_tasks():
    """Retrieve all tasks."""
    return Task.objects.all()

def get_task_by_id(task_id):
    """Retrieve a single task by ID."""
    return Task.objects.get(id=task_id)

def update_task(task_id, data):
    """Update an existing task."""
    task = Task.objects.get(id=task_id)
    task.title = data['title']
    task.description = data['description']
    task.start_date = data['start_date']
    task.deadline = data['deadline']
    task.status = data['status']
    task.project = Project.objects.get(id=data['project'])
    task.assignee = User.objects.get(id=data['assignee'])
    task.save()
    return task

def delete_task(task_id):
    """Delete a task."""
    Task.objects.filter(id=task_id).delete()
