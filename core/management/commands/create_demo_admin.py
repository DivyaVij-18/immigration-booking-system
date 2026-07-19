from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create temporary demo admin user"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        username = "demo_admin"
        email = "demo@example.com"
        password = "DemoPass123!"

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    "Demo admin already exists"
                )
            )
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Demo admin created successfully"
            )
        )