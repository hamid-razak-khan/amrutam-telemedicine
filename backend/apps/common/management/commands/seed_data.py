import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User, PatientProfile
from apps.doctors.models import DoctorProfile
from apps.availability.models import AvailabilitySlot
from apps.consultations.models import Consultation
from apps.prescriptions.models import Prescription
from apps.payments.models import Payment
from apps.audit.models import AuditLog

class Command(BaseCommand):
    help = 'Seeds synthetic test accounts, verified doctors, availability slots, consultations, and audit logs'

    def handle(self, *args, **options):
        self.stdout.write("Starting synthetic database seeding for Amrutam Telemedicine...")

        # 1. Admin
        admin, created = User.objects.get_or_create(
            email='admin@amrutam.co.in',
            defaults={
                'first_name': 'Chief',
                'last_name': 'Administrator',
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'account_status': User.STATUS_ACTIVE
            }
        )
        if created:
            admin.set_password('AdminPassword123!')
            admin.save()
            self.stdout.write(self.style.SUCCESS("Created Admin: admin@amrutam.co.in / AdminPassword123!"))

        # 2. Patients
        p1, created = User.objects.get_or_create(
            email='patient1@example.com',
            defaults={
                'first_name': 'Rahul',
                'last_name': 'Verma',
                'phone_number': '+919876543210',
                'role': User.ROLE_PATIENT,
                'account_status': User.STATUS_ACTIVE
            }
        )
        if created:
            p1.set_password('PatientPassword123!')
            p1.save()
            PatientProfile.objects.update_or_create(
                user=p1,
                defaults={
                    'gender': PatientProfile.GENDER_MALE,
                    'blood_group': 'O+',
                    'emergency_contact_name': 'Amit Verma',
                    'emergency_contact_phone': '+919876543211',
                    'medical_history_summary': 'Mild seasonal allergies, Pitta dominant constitution.'
                }
            )
            self.stdout.write(self.style.SUCCESS("Created Patient: patient1@example.com / PatientPassword123!"))

        p2, created = User.objects.get_or_create(
            email='patient2@example.com',
            defaults={
                'first_name': 'Sneha',
                'last_name': 'Patel',
                'phone_number': '+919812345678',
                'role': User.ROLE_PATIENT,
                'account_status': User.STATUS_ACTIVE
            }
        )
        if created:
            p2.set_password('PatientPassword123!')
            p2.save()
            PatientProfile.objects.update_or_create(
                user=p2,
                defaults={
                    'gender': PatientProfile.GENDER_FEMALE,
                    'blood_group': 'B+',
                    'emergency_contact_name': 'Kavita Patel',
                    'emergency_contact_phone': '+919812345679',
                    'medical_history_summary': 'Vata-Kapha imbalance, chronic lower back stiffness.'
                }
            )
            self.stdout.write(self.style.SUCCESS("Created Patient: patient2@example.com / PatientPassword123!"))

        # 3. Doctors
        doctors_meta = [
            {
                'email': 'dr.sharma@amrutam.co.in',
                'first': 'Rajesh',
                'last': 'Sharma',
                'phone': '+919822334455',
                'credentials': 'BAMS, MD (Ayurveda - Kayachikitsa)',
                'specialization': 'Kayachikitsa & Panchakarma',
                'bio': 'Senior Ayurvedic Consultant with over 12 years of clinical expertise treating chronic digestive and metabolic disorders using authentic classical formulations.',
                'exp': 12,
                'fee': 800.00
            },
            {
                'email': 'dr.ananya@amrutam.co.in',
                'first': 'Ananya',
                'last': 'Iyer',
                'phone': '+919833445566',
                'credentials': 'BAMS, Fellowship in Ayurvedic Dermatology',
                'specialization': 'Ayurvedic Dermatology & Hair Care',
                'bio': 'Specialist in holistic skin rejuvenation, chronic eczema, scalp disorders, and custom herbal skincare therapies.',
                'exp': 8,
                'fee': 650.00
            },
            {
                'email': 'dr.vikram@amrutam.co.in',
                'first': 'Vikram',
                'last': 'Malhotra',
                'phone': '+919844556677',
                'credentials': 'BAMS, MS (Ayurveda - Shalya Tantra)',
                'specialization': 'Joint Care & Musculoskeletal Disorders',
                'bio': 'Expert in managing arthritis, sciatica, spondylitis, and sports injuries through Marma therapy and targeted herbal oils.',
                'exp': 15,
                'fee': 1000.00
            },
            {
                'email': 'dr.priya@amrutam.co.in',
                'first': 'Priya',
                'last': 'Nair',
                'phone': '+919855667788',
                'credentials': 'BAMS, Certified Herbal Nutritionist',
                'specialization': 'Metabolic Health & Women Wellness',
                'bio': 'Focuses on hormonal harmony, PCOS management, dietary Ahara-Vihara counseling, and stress reduction through Rasayana herbs.',
                'exp': 6,
                'fee': 500.00
            }
        ]

        created_doctors = []
        for d in doctors_meta:
            u, created = User.objects.get_or_create(
                email=d['email'],
                defaults={
                    'first_name': d['first'],
                    'last_name': d['last'],
                    'phone_number': d['phone'],
                    'role': User.ROLE_DOCTOR,
                    'account_status': User.STATUS_ACTIVE
                }
            )
            if created:
                u.set_password('DoctorPassword123!')
                u.save()

            doc, _ = DoctorProfile.objects.update_or_create(
                user=u,
                defaults={
                    'credentials': d['credentials'],
                    'specialization': d['specialization'],
                    'biography': d['bio'],
                    'years_of_experience': d['exp'],
                    'consultation_fee': d['fee'],
                    'verification_status': DoctorProfile.STATUS_VERIFIED,
                    'active_status': True
                }
            )
            created_doctors.append(doc)
            self.stdout.write(self.style.SUCCESS(f"Created Doctor: {d['email']} / DoctorPassword123!"))

        # 4. Generate Slots for next 7 days
        now = timezone.now()
        base_date = now.replace(minute=0, second=0, microsecond=0)

        slot_times = [
            (9, 0, 9, 45),
            (10, 0, 10, 45),
            (11, 0, 11, 45),
            (14, 0, 14, 45),
            (15, 0, 15, 45),
            (16, 0, 16, 45),
        ]

        slots_created = 0
        for doc in created_doctors:
            for day_offset in range(0, 5):
                day = base_date + timedelta(days=day_offset)
                for start_h, start_m, end_h, end_m in slot_times:
                    slot_start = day.replace(hour=start_h, minute=start_m)
                    slot_end = day.replace(hour=end_h, minute=end_m)

                    if slot_start > now:
                        _, created = AvailabilitySlot.objects.get_or_create(
                            doctor=doc,
                            start_at=slot_start,
                            end_at=slot_end,
                            defaults={'status': AvailabilitySlot.STATUS_AVAILABLE}
                        )
                        if created:
                            slots_created += 1

        self.stdout.write(self.style.SUCCESS(f"Generated {slots_created} active availability slots across doctors."))

        # 5. Create a completed past consultation with prescription for patient1
        first_doc = created_doctors[0]
        past_slot, _ = AvailabilitySlot.objects.get_or_create(
            doctor=first_doc,
            start_at=now - timedelta(days=2, hours=3),
            end_at=now - timedelta(days=2, hours=2, minutes=15),
            defaults={'status': AvailabilitySlot.STATUS_BOOKED}
        )

        c_past, created = Consultation.objects.get_or_create(
            booking_reference="AMR-SEED-COMPLETED-01",
            defaults={
                'patient': p1,
                'doctor': first_doc,
                'slot': past_slot,
                'scheduled_start': past_slot.start_at,
                'scheduled_end': past_slot.end_at,
                'status': Consultation.STATUS_COMPLETED,
                'chief_complaint': 'Chronic indigestion and afternoon fatigue after meals.',
                'clinical_notes': 'Agni mandya detected. Prescribed Deepana & Pachana herbs. Advised warm water regimen.',
                'started_at': past_slot.start_at,
                'completed_at': past_slot.end_at
            }
        )

        if created:
            Prescription.objects.get_or_create(
                consultation=c_past,
                defaults={
                    'doctor': first_doc,
                    'patient': p1,
                    'diagnosis': 'Mandagni (Hypo-functioning digestive fire) with secondary Pitta aggravation.',
                    'medications': [
                        {
                            "name": "Amrutam Kuntal Care Herbal Malt",
                            "dosage": "1-2 tablespoons twice daily",
                            "duration": "30 days",
                            "instructions": "Mix with warm milk or lukewarm water before bedtime."
                        },
                        {
                            "name": "Triphala Churna (Classical)",
                            "dosage": "3 grams",
                            "duration": "21 days",
                            "instructions": "Take at night with warm water."
                        },
                        {
                            "name": "Avipattikar Churna",
                            "dosage": "1 tsp twice daily",
                            "duration": "14 days",
                            "instructions": "Consume 15 minutes before lunch and dinner."
                        }
                    ],
                    'lifestyle_recommendations': 'Avoid sour, excessively spicy, and stale foods. Eat dinner before 8:00 PM.',
                    'follow_up_date': (now + timedelta(days=14)).date(),
                    'additional_notes': 'Hydrate well. Regular 20-minute post-meal gentle stroll.'
                }
            )

            Payment.objects.get_or_create(
                consultation=c_past,
                defaults={
                    'patient': p1,
                    'amount': first_doc.consultation_fee,
                    'currency': 'INR',
                    'status': Payment.STATUS_COMPLETED,
                    'provider': 'SIMULATED_GATEWAY',
                    'provider_reference': 'SIM_PAY_SEED001'
                }
            )

        self.stdout.write(self.style.SUCCESS("Synthetic data seeding finished successfully!"))
