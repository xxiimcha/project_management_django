from .models import Project, TeamMember, Notification

def create_project(data, user):
    """ Create a new project and assign team members. """
    # Step 1: Create the project
    project = Project.objects.create(
        name=data['name'],
        description=data['description'],
        start_date=data['start_date'],
        deadline=data['deadline'],
        status="In Progress",
        created_by=user
    )

    # Step 2: Add team members and send notifications
    team_members_ids = data.getlist('team_members')  # Expecting team members as a list of IDs
    for member_id in team_members_ids:
        try:
            team_member = TeamMember.objects.get(id=member_id)
            project.team_members.add(team_member)

            # Send notification to the team member
            Notification.objects.create(
                user=team_member.user,
                message=f"You have been added to the project '{project.name}'."
            )
        except TeamMember.DoesNotExist:
            print(f"TeamMember with ID {member_id} does not exist. Skipping.")

    project.save()
    return project

def get_projects():
    """ Fetch all projects. """
    return Project.objects.all()

def delete_project(project_id):
    """ Delete a project by ID. """
    Project.objects.filter(id=project_id).delete()
