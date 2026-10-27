import uuid
import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from concurrent.futures import ThreadPoolExecutor

from apps.accounts.models import User
from apps.doctors.models import DoctorProfile
from apps.availability.models import AvailabilitySlot
from apps.consultations.models import Consultation

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db(transaction=True)
class TestBookingConcurrencyAndIdempotency:
    def test_idempotent_booking_retry_returns_cached_result(self, api_client):
        patient = User.objects.create_user(email='idemp_patient@example.com', password='Password123!', role=User.ROLE_PATIENT)
        doc_user = User.objects.create_user(email='idemp_doc@example.com', password='Password123!', role=User.ROLE_DOCTOR)
        doc = DoctorProfile.objects.create(user=doc_user, specialization='Ayurveda')

        now = timezone.now() + timedelta(days=1)
        slot = AvailabilitySlot.objects.create(
            doctor=doc,
            start_at=now,
            end_at=now + timedelta(minutes=45),
            status=AvailabilitySlot.STATUS_AVAILABLE
        )

        api_client.force_authenticate(user=patient)
        idempotency_key = str(uuid.uuid4())
        payload = {"slot_id": str(slot.id), "chief_complaint": "Joint pain"}

        # 1. First booking request
        resp1 = api_client.post('/api/v1/bookings', payload, HTTP_IDEMPOTENCY_KEY=idempotency_key)
        assert resp1.status_code == status.HTTP_201_CREATED
        booking_ref1 = resp1.data['booking']['booking_reference']

        # Verify only 1 consultation created
        assert Consultation.objects.filter(slot=slot).count() == 1

        # 2. Retry with identical Idempotency-Key and payload
        resp2 = api_client.post('/api/v1/bookings', payload, HTTP_IDEMPOTENCY_KEY=idempotency_key)
        assert resp2.status_code == status.HTTP_201_CREATED
        assert resp2.data['booking']['booking_reference'] == booking_ref1

        # Still only 1 consultation in database
        assert Consultation.objects.filter(slot=slot).count() == 1

    def test_idempotency_key_payload_mismatch_rejected(self, api_client):
        patient = User.objects.create_user(email='mismatch_patient@example.com', password='Password123!', role=User.ROLE_PATIENT)
        doc_user = User.objects.create_user(email='mismatch_doc@example.com', password='Password123!', role=User.ROLE_DOCTOR)
        doc = DoctorProfile.objects.create(user=doc_user, specialization='Ayurveda')

        now = timezone.now() + timedelta(days=1)
        slot1 = AvailabilitySlot.objects.create(doctor=doc, start_at=now, end_at=now + timedelta(minutes=45))
        slot2 = AvailabilitySlot.objects.create(doctor=doc, start_at=now + timedelta(hours=1), end_at=now + timedelta(hours=1, minutes=45))

        api_client.force_authenticate(user=patient)
        idempotency_key = str(uuid.uuid4())

        # First request with slot1
        resp1 = api_client.post('/api/v1/bookings', {"slot_id": str(slot1.id)}, HTTP_IDEMPOTENCY_KEY=idempotency_key)
        assert resp1.status_code == status.HTTP_201_CREATED

        # Second request re-using same key with slot2 (different payload!)
        resp2 = api_client.post('/api/v1/bookings', {"slot_id": str(slot2.id)}, HTTP_IDEMPOTENCY_KEY=idempotency_key)
        assert resp2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert 'IDEMPOTENCY_CONFLICT' in resp2.data['error']['code']

    def test_simultaneous_booking_race_condition_only_one_succeeds(self):
        """
        Simulate concurrent booking attempts for the exact same slot by two different patients.
        Tests transaction-safety, locking, and conflict handling.
        """
        patient1 = User.objects.create_user(email='race_p1@example.com', password='Password123!', role=User.ROLE_PATIENT)
        patient2 = User.objects.create_user(email='race_p2@example.com', password='Password123!', role=User.ROLE_PATIENT)

        doc_user = User.objects.create_user(email='race_doc@example.com', password='Password123!', role=User.ROLE_DOCTOR)
        doc = DoctorProfile.objects.create(user=doc_user, specialization='Ayurveda')

        now = timezone.now() + timedelta(days=2)
        slot = AvailabilitySlot.objects.create(
            doctor=doc,
            start_at=now,
            end_at=now + timedelta(minutes=45),
            status=AvailabilitySlot.STATUS_AVAILABLE
        )

        def attempt_booking(user):
            client = APIClient()
            client.force_authenticate(user=user)
            return client.post(
                '/api/v1/bookings',
                {"slot_id": str(slot.id), "chief_complaint": f"Complaint by {user.email}"},
                HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4())
            )

        # Run concurrent booking requests using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(attempt_booking, patient1)
            future2 = executor.submit(attempt_booking, patient2)
            res1 = future1.result()
            res2 = future2.result()

        status_codes = [res1.status_code, res2.status_code]

        # Exactly one booking should succeed (201 Created), and the other must be rejected (409 Conflict)
        assert status.HTTP_201_CREATED in status_codes, f"Expected 201 in {status_codes}"
        assert status.HTTP_409_CONFLICT in status_codes, f"Expected 409 in {status_codes}"

        # Verify database integrity: only 1 consultation created for this slot
        consultations = Consultation.objects.filter(slot=slot)
        assert consultations.count() == 1

        # Verify slot status is BOOKED
        slot.refresh_from_db()
        assert slot.status == AvailabilitySlot.STATUS_BOOKED
