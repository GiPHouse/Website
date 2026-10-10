from django.db import migrations

SEASONS = {0: "spring", 1: "fall"}
SLUG_MAX_LENGTH = 50


def deduplicate_project_slugs(apps, schema_editor):
    """
    Make project slugs globally unique before the unique constraint is added.

    Slugs used to be unique per semester only. For every slug used by more than one
    project, the project of the most recent semester keeps the slug and older projects
    get the semester appended, e.g. "my-project" becomes "my-project-2024fall".
    """
    Project = apps.get_model("projects", "Project")

    taken = set(Project.objects.values_list("slug", flat=True))
    projects = Project.objects.select_related("semester").order_by(
        "-semester__year", "-semester__season", "-pk"
    )

    seen = set()
    for project in projects:
        if project.slug not in seen:
            seen.add(project.slug)
            continue

        suffix = f"-{project.semester.year}{SEASONS.get(project.semester.season, project.semester.season)}"
        new_slug = f"{project.slug[: SLUG_MAX_LENGTH - len(suffix)]}{suffix}"
        if new_slug in taken:
            suffix = f"{suffix}-{project.pk}"
            new_slug = (
                f"{project.slug[: SLUG_MAX_LENGTH - len(suffix)]}{suffix}"
            )

        project.slug = new_slug
        project.save(update_fields=["slug"])
        taken.add(new_slug)
        seen.add(new_slug)


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0007_alter_project_description"),
    ]

    operations = [
        migrations.RunPython(
            deduplicate_project_slugs, migrations.RunPython.noop
        ),
    ]
