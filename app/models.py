from django.db import models
from django.contrib.auth.models import User

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
