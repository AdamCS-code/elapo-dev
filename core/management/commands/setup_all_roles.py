from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = "Setup all roles and permissions across apps"

    def handle(self, *args, **kwargs):
        apps = ['orders', 'payments', 'users']  # list all your apps with setup_roles
        for app in apps:
            try:
                call_command('setup_roles', app_label=app)
                self.stdout.write(self.style.SUCCESS(f"{app}: setup_roles done"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"{app}: failed with {e}"))

