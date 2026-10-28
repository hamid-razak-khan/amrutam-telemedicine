import os
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.doctors.models import DoctorProfile
from apps.availability.models import AvailabilitySlot


DEMO_DOCTOR_EMAILS = [
    'doctor1@example.com',
    'doctor2@example.com',
    'doctor3@example.com',
    'doctor4@example.com',
]

DEMO_DOCTORS_DATA = [
    {
        'email': 'doctor1@example.com',
        'first_name': 'Ananya',
        'last_name': 'Sharma',
        'phone_number': '+919811100001',
        'specialization': 'General Physician',
        'credentials': 'MBBS, MD (General Medicine) — Demonstration Profile',
        'years_of_experience': 8,
        'consultation_fee': 600.00,
        'license_number': 'DEMO-DOC-001',
        'biography': 'Demonstration Profile: Experienced General Physician with 8 years of clinical expertise providing comprehensive primary care, diagnostic assessments, and online consultations.',
        'slot_hours': [(9, 10), (10, 11), (11, 12)],  # Morning slots
        'days_ahead': [1, 2, 3, 4],
    },
    {
        'email': 'doctor2@example.com',
        'first_name': 'Rahul',
        'last_name': 'Menon',
        'phone_number': '+919811100002',
        'specialization': 'Dermatology',
        'credentials': 'MBBS, MD (Dermatology) — Demonstration Profile',
        'years_of_experience': 7,
        'consultation_fee': 750.00,
        'license_number': 'DEMO-DOC-002',
        'biography': 'Demonstration Profile: Consultant Dermatologist with 7 years of specialized practice diagnosing skin and scalp conditions, preventive dermatology, and clinical skin regimens.',
        'slot_hours': [(14, 15), (15, 16), (16, 17)],  # Afternoon slots
        'days_ahead': [1, 2, 3, 5],
    },
    {
        'email': 'doctor3@example.com',
        'first_name': 'Priya',
        'last_name': 'Nair',
        'phone_number': '+919811100003',
        'specialization': 'Pediatrics',
        'credentials': 'MBBS, MD (Pediatrics) — Demonstration Profile',
        'years_of_experience': 10,
        'consultation_fee': 700.00,
        'license_number': 'DEMO-DOC-003',
        'biography': 'Demonstration Profile: Senior Pediatrician with 10 years of clinical experience in child health, developmental milestones, adolescent counseling, and family telemedicine.',
        'slot_hours': [(10, 11), (11, 12), (16, 17)],  # Selected weekday and weekend slots
        'days_ahead': [1, 3, 5, 6],
    },
    {
        'email': 'doctor4@example.com',
        'first_name': 'Arjun',
        'last_name': 'Reddy',
        'phone_number': '+919811100004',
        'specialization': 'Cardiology',
        'credentials': 'MBBS, MD, DM (Cardiology) — Demonstration Profile',
        'years_of_experience': 12,
        'consultation_fee': 950.00,
        'license_number': 'DEMO-DOC-004',
        'biography': 'Demonstration Profile: Consultant Cardiologist with 12 years of practice in cardiovascular risk prevention, hypertension management, and lifestyle heart wellness.',
        'slot_hours': [(17, 18), (18, 19), (19, 20)],  # Evening slots
        'days_ahead': [1, 2, 4, 5],
    },
]


class Command(BaseCommand):
    help = 'Seeds exactly four realistic demonstration doctor accounts with approved status and upcoming availability slots.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Safely remove only the four demonstration doctor accounts and their slots.'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force execution in non-DEBUG environments.'
        )

    def handle(self, *args, **options):
        # Production environment protection
        is_production = os.getenv('ENVIRONMENT', '').lower() == 'production' or os.getenv('DJANGO_ENV', '').lower() == 'production'
        if is_production and not options.get('force'):
            raise CommandError("Refusing to run seed_demo_doctors against a production environment. Use development or staging.")

        if options.get('clean'):
            self.stdout.write(self.style.WARNING("Removing only the four demonstration doctor records..."))
            with transaction.atomic():
                deleted_count, _ = User.objects.filter(email__in=DEMO_DOCTOR_EMAILS).delete()
            self.stdout.write(self.style.SUCCESS(f"Cleaned up demonstration accounts ({deleted_count} objects removed)."))
            return

        self.stdout.write(self.style.NOTICE("Provisioning 4 synthetic demonstration doctor accounts..."))

        demo_password = os.getenv('DEMO_DOCTOR_PASSWORD', 'DoctorSecure2026!')

        created_count = 0
        updated_count = 0
        total_slots_created = 0

        with transaction.atomic():
            now = timezone.now()
            base_date = now.date()

            for doc_data in DEMO_DOCTORS_DATA:
                email = doc_data['email']
                user, user_created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': doc_data['first_name'],
                        'last_name': doc_data['last_name'],
                        'phone_number': doc_data['phone_number'],
                        'role': User.ROLE_DOCTOR,
                        'account_status': User.STATUS_ACTIVE,
                        'is_active': True,
                    }
                )

                if user_created:
                    user.set_password(demo_password)
                    user.save()
                    created_count += 1
                else:
                    # Update profile fields without overwriting user password if already set
                    user.first_name = doc_data['first_name']
                    user.last_name = doc_data['last_name']
                    user.phone_number = doc_data['phone_number']
                    user.role = User.ROLE_DOCTOR
                    user.account_status = User.STATUS_ACTIVE
                    user.is_active = True
                    user.save(update_fields=['first_name', 'last_name', 'phone_number', 'role', 'account_status', 'is_active'])
                    updated_count += 1

                # Doctor Profile with APPROVED verification status
                profile, prof_created = DoctorProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        'license_number': doc_data['license_number'],
                        'credentials': doc_data['credentials'],
                        'specialization': doc_data['specialization'],
                        'biography': doc_data['biography'],
                        'years_of_experience': doc_data['years_of_experience'],
                        'consultation_fee': doc_data['consultation_fee'],
                        'verification_status': DoctorProfile.STATUS_APPROVED,
                        'active_status': True,
                        'approved_at': now,
                    }
                )

                # Generate upcoming availability slots
                for day_offset in doc_data['days_ahead']:
                    slot_date = base_date + timedelta(days=day_offset)
                    for start_hour, end_hour in doc_data['slot_hours']:
                        start_dt = timezone.make_aware(
                            timezone.datetime(slot_date.year, slot_date.month, slot_date.day, start_hour, 0)
                        )
                        end_dt = timezone.make_aware(
                            timezone.datetime(slot_date.year, slot_date.month, slot_date.day, end_hour, 0)
                        )

                        # Avoid creating duplicate slots
                        existing_slot = AvailabilitySlot.objects.filter(
                            doctor=profile,
                            start_at=start_dt,
                            end_at=end_dt
                        ).first()

                        if not existing_slot:
                            AvailabilitySlot.objects.create(
                                doctor=profile,
                                start_at=start_dt,
                                end_at=end_dt,
                                status=AvailabilitySlot.STATUS_AVAILABLE
                            )
                            total_slots_created += 1

                action_str = "Created" if user_created else "Updated"
                self.stdout.write(self.style.SUCCESS(
                    f"[+] {action_str} Dr. {user.first_name} {user.last_name} ({profile.specialization}) - {user.email}"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"\nDemonstration Doctors Provisioning Completed:\n"
            f" - Accounts Created: {created_count}\n"
            f" - Accounts Updated: {updated_count}\n"
            f" - New Availability Slots Seeded: {total_slots_created}\n"
            f" - Status: All 4 accounts set to APPROVED and searchable in patient directory."
        ))
        self.stdout.write(self.style.NOTICE(
            "To remove these synthetic demonstration accounts at any time, run:\n"
            "  python manage.py seed_demo_doctors --clean\n"
        ))
