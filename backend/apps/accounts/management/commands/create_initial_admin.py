import os
import sys
import getpass
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.accounts.services.auth_service import AuthService


class Command(BaseCommand):
    help = 'Securely provisions the initial platform administrator account with ADMIN role and superuser privileges.'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Administrator email address (defaults to admin@amrutam.co.in)')
        parser.add_argument('--password', type=str, help='Administrator password (secure environments only)')
        parser.add_argument('--first-name', type=str, default='Chief', help='Administrator first name')
        parser.add_argument('--last-name', type=str, default='Administrator', help='Administrator last name')
        parser.add_argument('--reset-password', action='store_true', help='Update password for existing administrator if provided')
        parser.add_argument('--noinput', '--no-input', action='store_true', help='Do not prompt for input')

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing secure administrator provisioning..."))

        email = options.get('email') or os.getenv('INITIAL_ADMIN_EMAIL') or 'admin@amrutam.co.in'
        password = options.get('password') or os.getenv('INITIAL_ADMIN_PASSWORD')
        first_name = options.get('first_name') or 'Chief'
        last_name = options.get('last_name') or 'Administrator'
        no_input = options.get('noinput')

        # Interactive prompts if required fields are missing
        if not email:
            if no_input:
                email = 'admin@amrutam.co.in'
            else:
                email = input("Administrator Email [admin@amrutam.co.in]: ").strip() or 'admin@amrutam.co.in'

        clean_email = email.strip().lower()
        if not clean_email or '@' not in clean_email:
            raise CommandError("A valid email address is required.")

        # Check existing administrator
        existing_user = User.objects.filter(email=clean_email).first()
        if existing_user:
            if existing_user.role == User.ROLE_ADMIN and existing_user.is_superuser:
                if options.get('reset_password') and password:
                    existing_user.set_password(password)
                    existing_user.save()
                    self.stdout.write(self.style.SUCCESS(f"Administrator '{clean_email}' password updated securely."))
                    return
                self.stdout.write(self.style.SUCCESS(f"Administrator account '{clean_email}' verified (Role: ADMINISTRATOR, Status: ACTIVE). Existing credentials preserved."))
                return
            else:
                self.stdout.write(self.style.NOTICE(f"User '{clean_email}' exists. Upgrading to platform ADMINISTRATOR."))
                existing_user.role = User.ROLE_ADMIN
                existing_user.is_staff = True
                existing_user.is_superuser = True
                existing_user.account_status = User.STATUS_ACTIVE
                if password:
                    existing_user.set_password(password)
                existing_user.save()
                self.stdout.write(self.style.SUCCESS(f"User '{clean_email}' successfully upgraded to ADMINISTRATOR."))
                return

        # Secure password prompting
        if not password:
            if no_input:
                raise CommandError("Administrator password must be provided via --password or INITIAL_ADMIN_PASSWORD environment variable when --noinput is set.")
            
            while True:
                password = getpass.getpass("Administrator Password: ")
                password_confirm = getpass.getpass("Confirm Administrator Password: ")

                if password != password_confirm:
                    self.stdout.write(self.style.ERROR("Passwords do not match. Please try again."))
                    continue

                try:
                    validate_password(password)
                    break
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f"Password validation error: {', '.join(e.messages)}"))

        user, created = AuthService.create_initial_admin(
            email=clean_email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Platform administrator '{clean_email}' created successfully!"))
            self.stdout.write(self.style.WARNING("IMPORTANT SECURITY NOTICE: The administrator must configure Multi-Factor Authentication (MFA) via /api/v1/auth/mfa/setup upon initial login."))
        else:
            self.stdout.write(self.style.WARNING(f"Administrator '{clean_email}' already exists."))
