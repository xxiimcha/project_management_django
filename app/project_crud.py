from .models import Project, TeamMember

def create_project(data, user):
    """ Create a new project and assign team members. """
    # Create the project instance
    project = Project.objects.create(
        name=data['name'],
        description=data['description'],
        start_date=data['start_date'],
        deadline=data['deadline'],
        status="In Progress",
        created_by=user
    )

    # Add team members
    team_members_ids = data.getlist('team_members')  # Expecting team members as a list of IDs
    for member_id in team_members_ids:
        team_member = TeamMember.objects.get(id=member_id)
        project.team_members.add(team_member)

    project.save()
    return project

def get_projects():
    """ Fetch all projects. """
    return Project.objects.all()

def delete_project(project_id):
    """ Delete a project by ID. """
    Project.objects.filter(id=project_id).delete()
