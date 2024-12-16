from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('project_manager', 'Project Manager'),
        ('team_member', 'Team Member'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='team_member')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
# Team Members Table
class TeamMember(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="team_member")
    added_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="added_members")
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} (Added by {self.added_by.username})"

# Project Table
class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField()
    deadline = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('In Progress', 'In Progress'),
            ('Completed', 'Completed'),
            ('On Hold', 'On Hold'),
        ],
        default='In Progress'
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_projects")
    team_members = models.ManyToManyField(TeamMember, related_name="projects")
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (Status: {self.status})"

# Task Model
class Task(models.Model):
    STATUS_CHOICES = [
        ('not-started', 'Not Started'),
        ('in-progress', 'In Progress'),
        ('done', 'Done'),
        ('urgent', 'Urgent'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    title = models.CharField(max_length=255)  # Task title
    description = models.TextField()  # Task description
    due_date = models.DateField()  # Task deadline
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not-started')  # Task status
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')  # Task priority
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")  # Associated project
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")  # Assigned user
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_tasks")  # Creator user ID
    date_created = models.DateTimeField(auto_now_add=True)  # Date the task was created
    date_updated = models.DateTimeField(auto_now=True)  # Date the task was last updated

    def __str__(self):
        return f"{self.title} (Status: {self.status}, Priority: {self.priority})"
    

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message}"