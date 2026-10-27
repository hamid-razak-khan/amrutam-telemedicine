import pytest
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.accounts.models import User, PatientProfile
from apps.doctors.models import DoctorProfile
from apps.availability.models import AvailabilitySlot
from apps.consultations.models import Consultation
from apps.prescriptions.models import Prescription
from apps.common.models import IdempotencyKey

@pytest.mark.django_db
class TestUserModel:
    def test_create_patient_user(self):
        user = User.objects.create_user(
            email='testpatient@example.com',
            password='TestPassword123!',
            first_name='Aarav',
            last_name='Kumar',
            role=User.ROLE_PATIENT
        )
        assert user.email == 'testpatient@example.com'
        assert user.role == User.ROLE_PATIENT
        assert user.check_password('TestPassword123!')
        assert user.is_active is True
        assert user.full_name == 'Aarav Kumar'

    def test_create_superuser_role(self):
        admin = User.objects.create_superuser(
            email='superadmin@example.com',
            password='AdminPassword123!',
            first_name='System',
            last_name='Admin'
        )
        assert admin.role == User.ROLE_ADMIN
        assert admin.is_staff is True
        assert admin.is_superuser is True

@pytest.mark.django_db
class TestAvailabilitySlotModel:
    def test_slot_end_time_before_start_time_raises_error(self):
        doc_user = User.objects.create_user(
            email='doc1@example.com',
            password='Password123!',
            first_name='Dev',
            last_name='Gupta',
            role=User.ROLE_DOCTOR
        )
        doc = DoctorProfile.objects.create(
            user=doc_user,
            credentials='BAMS',
            specialization='Ayurveda',
            consultation_fee=500.00
        )
        now = timezone.now() + timedelta(days=1)
        # End time before start time
        slot = AvailabilitySlot(
            doctor=doc,
            start_at=now + timedelta(hours=1),
            end_at=now,
            status=AvailabilitySlot.STATUS_AVAILABLE
        )
        with pytest.raises(ValidationError):
            slot.full_clean()

    def test_overlapping_slots_rejected(self):
        doc_user = User.objects.create_user(
            email='doc2@example.com',
            password='Password123!',
            first_name='Anil',
            last_name='Sharma',
            role=User.ROLE_DOCTOR
        )
        doc = DoctorProfile.objects.create(
            user=doc_user,
            credentials='BAMS',
            specialization='Panchakarma'
        )
        now = timezone.now() + timedelta(days=2)
        # Create first slot: 10:00 to 11:00
        AvailabilitySlot.objects.create(
            doctor=doc,
            start_at=now.replace(hour=10, minute=0),
            end_at=now.replace(hour=11, minute=0),
            status=AvailabilitySlot.STATUS_AVAILABLE
        )
        # Attempt overlapping slot: 10:30 to 11:30
        overlapping = AvailabilitySlot(
            doctor=doc,
            start_at=now.replace(hour=10, minute=30),
            end_at=now.replace(hour=11, minute=30),
            status=AvailabilitySlot.STATUS_AVAILABLE
        )
        with pytest.raises(ValidationError):
            overlapping.full_clean()

@pytest.mark.django_db
class TestConsultationStateTransitions:
    def test_valid_state_transitions(self):
        p = User.objects.create_user(email='p_trans@example.com', password='Password123!')
        d_user = User.objects.create_user(email='d_trans@example.com', password='Password123!', role=User.ROLE_DOCTOR)
        d = DoctorProfile.objects.create(user=d_user, specialization='Ayurveda')
        now = timezone.now() + timedelta(days=1)
        slot = AvailabilitySlot.objects.create(doctor=d, start_at=now, end_at=now + timedelta(minutes=45))

        consultation = Consultation.objects.create(
            booking_reference='AMR-TEST-TRANS',
            patient=p,
            doctor=d,
            slot=slot,
            scheduled_start=slot.start_at,
            scheduled_end=slot.end_at,
            status=Consultation.STATUS_BOOKED
        )

        assert consultation.can_transition_to(Consultation.STATUS_IN_PROGRESS)
        consultation.transition_to(Consultation.STATUS_IN_PROGRESS, actor=d_user)
        assert consultation.status == Consultation.STATUS_IN_PROGRESS
        assert consultation.started_at is not None

        assert consultation.can_transition_to(Consultation.STATUS_COMPLETED)
        consultation.transition_to(Consultation.STATUS_COMPLETED, actor=d_user)
        assert consultation.status == Consultation.STATUS_COMPLETED
        assert consultation.completed_at is not None

        # Terminal state cannot transition to IN_PROGRESS
        assert not consultation.can_transition_to(Consultation.STATUS_IN_PROGRESS)
        with pytest.raises(ValidationError):
            consultation.transition_to(Consultation.STATUS_IN_PROGRESS)
