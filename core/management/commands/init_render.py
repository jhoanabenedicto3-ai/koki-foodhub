"""
Initialize Render deployment: run migrations and create superuser if needed
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command
import os


class Command(BaseCommand):
    help = 'Initialize Render deployment with migrations and default admin user'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Initializing Render deployment...')

        # Run migrations
        self.stdout.write('📦 Running database migrations...')
        try:
            call_command('migrate', verbosity=1)
            self.stdout.write(self.style.SUCCESS('✅ Migrations completed'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Migration issue: {e}'))

        # Create superuser if it doesn't exist
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            self.stdout.write('👤 Creating admin user...')
            try:
                User.objects.create_superuser(
                    username='admin',
                    email=os.getenv('ADMIN_EMAIL', 'admin@koki-foodhub.com'),
                    password=os.getenv('ADMIN_PASSWORD', 'admin123')
                )
                self.stdout.write(self.style.SUCCESS('✅ Admin user created'))
                self.stdout.write('📝 Credentials:')
                self.stdout.write(f'   Username: admin')
                self.stdout.write(f'   Password: {os.getenv("ADMIN_PASSWORD", "admin123")}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️ Admin user creation issue: {e}'))
        else:
            self.stdout.write('ℹ️ Admin user already exists')

        self.stdout.write(self.style.SUCCESS('✅ Render initialization complete!'))
