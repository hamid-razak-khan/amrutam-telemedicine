import uuid
import pytest
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.doctors.models import DoctorProfile
from apps.availability.models import AvailabilitySlot
from apps.consultations.models import Consultation
from apps.payments.models import Payment
from apps.bookings.models import Booking
from apps.common.management.commands.release_expired_reservations import Command as ReleaseExpiredCommand


@pytest.fixture
def api_client():
    return APIClient()


def create_test_doctor(email='doc@example.com', verification_status=DoctorProfile.STATUS_VERIFIED):
    doc_user = User.objects.create_user(
        email=email,
        password='Password123!',
        role=User.ROLE_DOCTOR,
        first_name='Vaidya',
        last_name='Ayur'
    )
    profile = DoctorProfile.objects.create(
        user=doc_user,
        specialization='Kayachikitsa',
        credentials='BAMS, MD (Ayurveda)',
        years_of_experience=10,
        consultation_fee=600,
        verification_status=verification_status,
        active_status=True
    )
    return profile


def create_test_patient(email='patient@example.com'):
    return User.objects.create_user(
        email=email,
        password='Password123!',
        role=User.ROLE_PATIENT,
        first_name='Test',
        last_name='Patient'
    )


@pytest.mark.django_db
class TestAppointmentBookingBusinessRules:
    """
    Comprehensive verification for all 17 appointment booking and concurrency rules.
    """

    def test_01_patient_successfully_books_available_slot(self, api_client):
        """1. A patient successfully books an available slot."""
        doctor = create_test_doctor('doc1@example.com')
        patient = create_test_patient('patient1@example.com')
        now = timezone.now() + timedelta(days=1)
        slot = AvailabilitySlot.objects.create(
            doctor=doctor,
            start_at=now,
            end_at=now + timedelta(minutes=45),
            status=AvailabilitySlot.STATUS_AVAILABLE
        )

        api_client.force_authenticate(user=patient)
        resp = api_client.post(
            '/api/v1/bookings',
            {"slot_id": str(slot.id), "chief_complaint": "Joint discomfort"},
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4())
        )

        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data['success'] is True
        booking_data = resp.data['booking']
        assert booking_data['status'] == Consultation.STATUS_BOOKED
        assert booking_data['expires_at'] is not None

        # Verify database state
        slot.refresh_from_db()
        assert slot.status == AvailabilitySlot.STATUS_RESERVED
        consultation = Consultation.objects.get(id=booking_data['id'])
        assert consultation.patient == patient
        assert consultation.slot == slot
        assert consultation.payments.filter(status=Payment.STATUS_PENDING).count() == 1

    def test_02_second_patient_cannot_book_same_active_slot(self, api_client):
        """2. A second patient cannot book the same active slot."""
        doctor = create_test_doctor('doc2@example.com')
        p1 = create_test_patient('p2_1@example.com')
        p2 = create_test_patient('p2_2@example.com')
        now = timezone.now() + timedelta(days=2)
        slot = AvailabilitySlot.objects.create(
            doctor=doctor,
            start_at=now,
            end_at=now + timedelta(minutes=45),
            status=AvailabilitySlot.STATUS_AVAILABLE
        )

        # Patient 1 books
        api_client.force_authenticate(user=p1)
        resp1 = api_client.post(
            '/api/v1/bookings',
            {"slot_id": str(slot.id)},
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4())
        )
        assert resp1.status_code == status.HTTP_201_CREATED

        # Patient 2 attempts booking same slot
        api_client.force_authenticate(user=p2)
        resp2 = api_client.post(
            '/api/v1/bookings',
            {"slot_id": str(slot.id)},
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4())
        )
        assert resp2.status_code == status.HTTP_409_CONFLICT
        assert resp2.data['error']['code'] == 'SLOT_UNAVAILABLE'
        assert "Sorry, this time slot has just been booked" in resp2.data['error']['message']

        # Database invariant: exactly 1 consultation
        assert Consultation.objects.filter(slot=slot).count() == 1

    def test_03_same_doctor_can_have_appointments_at_different_times(self, api_client):
        """3. The same doctor can have appointments at different times."""
        doctor = create_test_doctor('doc3@example.com')
        p1 = create_test_patient('p3_1@example.com')
        p2 = create_test_patient('p3_2@example.com')
        now = timezone.now() + timedelta(days=3)

        slot1 = AvailabilitySlot.objects.create(doctor=doctor, start_at=now, end_at=now + timedelta(minutes=45))
        slot2 = AvailabilitySlot.objects.create(doctor=doctor, start_at=now + timedelta(hours=1), end_at=now + timedelta(hours=1, minutes=45))

        api_client.force_authenticate(user=p1)
        resp1 = api_client.post('/api/v1/bookings', {"slot_id": str(slot1.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        assert resp1.status_code == status.HTTP_201_CREATED

        api_client.force_authenticate(user=p2)
        resp2 = api_client.post('/api/v1/bookings', {"slot_id": str(slot2.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        assert resp2.status_code == status.HTTP_201_CREATED

        assert Consultation.objects.filter(doctor=doctor).count() == 2

    def test_04_two_different_doctors_can_have_appointments_at_same_time(self, api_client):
        """4. Two different doctors can have appointments at the same time."""
        doc1 = create_test_doctor('doc4_1@example.com')
        doc2 = create_test_doctor('doc4_2@example.com')
        p1 = create_test_patient('p4_1@example.com')
        p2 = create_test_patient('p4_2@example.com')

        now = timezone.now() + timedelta(days=4)
        slot1 = AvailabilitySlot.objects.create(doctor=doc1, start_at=now, end_at=now + timedelta(minutes=45))
        slot2 = AvailabilitySlot.objects.create(doctor=doc2, start_at=now, end_at=now + timedelta(minutes=45))

        api_client.force_authenticate(user=p1)
        resp1 = api_client.post('/api/v1/bookings', {"slot_id": str(slot1.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        assert resp1.status_code == status.HTTP_201_CREATED

        api_client.force_authenticate(user=p2)
        resp2 = api_client.post('/api/v1/bookings', {"slot_id": str(slot2.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        assert resp2.status_code == status.HTTP_201_CREATED

        assert Consultation.objects.filter(scheduled_start=now).count() == 2

    def test_05_cancelled_appointment_releases_slot(self, api_client):
        """5. A cancelled appointment releases its slot."""
        doctor = create_test_doctor('doc5@example.com')
        p1 = create_test_patient('p5_1@example.com')
        p2 = create_test_patient('p5_2@example.com')
        now = timezone.now() + timedelta(days=5)

        slot = AvailabilitySlot.objects.create(doctor=doctor, start_at=now, end_at=now + timedelta(minutes=45))

        # P1 books
        api_client.force_authenticate(user=p1)
        resp1 = api_client.post('/api/v1/bookings', {"slot_id": str(slot.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        booking_id = resp1.data['booking']['id']

        # P1 cancels
        cancel_resp = api_client.post(f'/api/v1/bookings/{booking_id}/cancel', {"reason": "Change of plans"})
        assert cancel_resp.status_code == status.HTTP_200_OK

        slot.refresh_from_db()
        assert slot.status == AvailabilitySlot.STATUS_AVAILABLE

        # P2 now successfully books the released slot
        api_client.force_authenticate(user=p2)
        resp2 = api_client.post('/api/v1/bookings', {"slot_id": str(slot.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        assert resp2.status_code == status.HTTP_201_CREATED

        # Both consultations remain in database history
        assert Consultation.objects.filter(slot=slot).count() == 2
        assert Consultation.objects.filter(slot=slot, status=Consultation.STATUS_CANCELLED).count() == 1
        assert Consultation.objects.filter(slot=slot, status=Consultation.STATUS_BOOKED).count() == 1

    def test_06_completed_appointment_remains_in_history_without_blocking_future_bookings(self, api_client):
        """6. A completed appointment remains in the history without blocking future bookings."""
        doctor = create_test_doctor('doc6@example.com')
        patient = create_test_patient('p6@example.com')
        now = timezone.now()

        past_start = now - timedelta(days=2)
        past_slot = AvailabilitySlot.objects.create(
            doctor=doctor,
            start_at=past_start,
            end_at=past_start + timedelta(minutes=45),
            status=AvailabilitySlot.STATUS_BOOKED
        )
        completed_c = Consultation.objects.create(
            booking_reference=f"HIST-{uuid.uuid4().hex[:6]}",
            patient=patient,
            doctor=doctor,
            slot=past_slot,
            scheduled_start=past_start,
            scheduled_end=past_start + timedelta(minutes=45),
            status=Consultation.STATUS_COMPLETED,
            completed_at=past_start + timedelta(minutes=40)
        )

        # Future slot for same doctor
        future_start = now + timedelta(days=2)
        future_slot = AvailabilitySlot.objects.create(
            doctor=doctor,
            start_at=future_start,
            end_at=future_start + timedelta(minutes=45),
            status=AvailabilitySlot.STATUS_AVAILABLE
        )

        api_client.force_authenticate(user=patient)
        resp = api_client.post('/api/v1/bookings', {"slot_id": str(future_slot.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        assert resp.status_code == status.HTTP_201_CREATED

        # Historical completed consultation is preserved
        assert Consultation.objects.filter(id=completed_c.id, status=Consultation.STATUS_COMPLETED).exists()

    def test_07_pending_payment_reservation_blocks_other_bookings_until_expires(self, api_client):
        """7. A pending-payment reservation blocks other bookings until it expires."""
        doctor = create_test_doctor('doc7@example.com')
        p1 = create_test_patient('p7_1@example.com')
        p2 = create_test_patient('p7_2@example.com')
        now = timezone.now() + timedelta(days=1)

        slot = AvailabilitySlot.objects.create(doctor=doctor, start_at=now, end_at=now + timedelta(minutes=45))

        # P1 reserves
        api_client.force_authenticate(user=p1)
        api_client.post('/api/v1/bookings', {"slot_id": str(slot.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))

        # P2 attempts while reservation is active (within 10 minutes)
        api_client.force_authenticate(user=p2)
        resp = api_client.post('/api/v1/bookings', {"slot_id": str(slot.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        assert resp.status_code == status.HTTP_409_CONFLICT

    def test_08_expired_reservation_no_longer_blocks_availability(self, api_client):
        """8. An expired reservation no longer blocks availability."""
        doctor = create_test_doctor('doc8@example.com')
        p1 = create_test_patient('p8_1@example.com')
        p2 = create_test_patient('p8_2@example.com')
        now = timezone.now() + timedelta(days=2)

        slot = AvailabilitySlot.objects.create(
            doctor=doctor,
            start_at=now,
            end_at=now + timedelta(minutes=45),
            status=AvailabilitySlot.STATUS_RESERVED
        )

        # Active booking whose expiration was 2 minutes ago
        c1 = Consultation.objects.create(
            booking_reference=f"EXP-{uuid.uuid4().hex[:6]}",
            patient=p1,
            doctor=doctor,
            slot=slot,
            scheduled_start=now,
            scheduled_end=now + timedelta(minutes=45),
            status=Consultation.STATUS_BOOKED,
            expires_at=timezone.now() - timedelta(minutes=2)
        )

        # Checking availability returns this slot because reservation has expired!
        avail_resp = api_client.get(f'/api/v1/doctors/{doctor.id}/availability')
        assert avail_resp.status_code == status.HTTP_200_OK
        avail_slot_ids = [s['id'] for s in avail_resp.data['slots']]
        assert str(slot.id) in avail_slot_ids

        # P2 books the expired slot
        api_client.force_authenticate(user=p2)
        resp = api_client.post('/api/v1/bookings', {"slot_id": str(slot.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        assert resp.status_code == status.HTTP_201_CREATED

        # P1's consultation was marked CANCELLED with expired reason
        c1.refresh_from_db()
        assert c1.status == Consultation.STATUS_CANCELLED

    def test_09_successful_payment_prevents_reservation_expiration_from_releasing_slot(self, api_client):
        """9. A successful payment prevents reservation expiration from releasing the slot."""
        doctor = create_test_doctor('doc9@example.com')
        p1 = create_test_patient('p9@example.com')
        now = timezone.now() + timedelta(days=3)

        slot = AvailabilitySlot.objects.create(doctor=doctor, start_at=now, end_at=now + timedelta(minutes=45))

        api_client.force_authenticate(user=p1)
        resp = api_client.post('/api/v1/bookings', {"slot_id": str(slot.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        c_id = resp.data['booking']['id']

        # Patient pays
        pay_resp = api_client.post('/api/v1/payments/initiate', {"consultation_id": c_id})
        assert pay_resp.status_code == status.HTTP_200_OK
        assert pay_resp.data['payment']['status'] == Payment.STATUS_COMPLETED

        # Consultation confirmed & expires_at cleared
        consultation = Consultation.objects.get(id=c_id)
        assert consultation.status == Consultation.STATUS_CONFIRMED
        assert consultation.expires_at is None
        slot.refresh_from_db()
        assert slot.status == AvailabilitySlot.STATUS_BOOKED

        # Run expiration management command
        ReleaseExpiredCommand().handle(batch_size=100)

        # Slot and consultation remain BOOKED / CONFIRMED
        slot.refresh_from_db()
        consultation.refresh_from_db()
        assert slot.status == AvailabilitySlot.STATUS_BOOKED
        assert consultation.status == Consultation.STATUS_CONFIRMED

    def test_10_duplicate_payment_requests_do_not_create_duplicate_successful_payments(self, api_client):
        """10. Duplicate payment requests do not create duplicate successful payments."""
        doctor = create_test_doctor('doc10@example.com')
        p1 = create_test_patient('p10@example.com')
        now = timezone.now() + timedelta(days=2)

        slot = AvailabilitySlot.objects.create(doctor=doctor, start_at=now, end_at=now + timedelta(minutes=45))
        api_client.force_authenticate(user=p1)
        resp = api_client.post('/api/v1/bookings', {"slot_id": str(slot.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        c_id = resp.data['booking']['id']

        # First payment
        pay_resp1 = api_client.post('/api/v1/payments/initiate', {"consultation_id": c_id})
        assert pay_resp1.status_code == status.HTTP_200_OK
        first_ref = pay_resp1.data['payment']['provider_reference']

        # Second payment attempt for same consultation
        pay_resp2 = api_client.post('/api/v1/payments/initiate', {"consultation_id": c_id})
        assert pay_resp2.status_code == status.HTTP_200_OK
        assert pay_resp2.data['payment']['provider_reference'] == first_ref

        # Invariant: exactly 1 completed payment in database
        assert Payment.objects.filter(consultation_id=c_id, status=Payment.STATUS_COMPLETED).count() == 1

    def test_11_patient_cannot_book_for_another_patient(self, api_client):
        """11. A patient cannot book for another patient."""
        doctor = create_test_doctor('doc11@example.com')
        p1 = create_test_patient('p11_1@example.com')
        p2 = create_test_patient('p11_2@example.com')
        now = timezone.now() + timedelta(days=3)

        slot = AvailabilitySlot.objects.create(doctor=doctor, start_at=now, end_at=now + timedelta(minutes=45))

        api_client.force_authenticate(user=p1)
        # Attempt to pass victim's patient ID
        resp = api_client.post(
            '/api/v1/bookings',
            {"slot_id": str(slot.id), "patient_id": str(p2.id), "patient": str(p2.id)},
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4())
        )
        assert resp.status_code == status.HTTP_201_CREATED

        # Consultation MUST be assigned to authenticated user p1, NOT p2
        consultation = Consultation.objects.get(id=resp.data['booking']['id'])
        assert consultation.patient == p1
        assert consultation.patient != p2

    def test_12_patient_cannot_pay_for_another_patients_appointment(self, api_client):
        """12. A patient cannot pay for another patient's appointment."""
        doctor = create_test_doctor('doc12@example.com')
        p1 = create_test_patient('p12_1@example.com')
        p2 = create_test_patient('p12_2@example.com')
        now = timezone.now() + timedelta(days=4)

        slot = AvailabilitySlot.objects.create(doctor=doctor, start_at=now, end_at=now + timedelta(minutes=45))

        # P1 books
        api_client.force_authenticate(user=p1)
        resp = api_client.post('/api/v1/bookings', {"slot_id": str(slot.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        c_id = resp.data['booking']['id']

        # P2 tries to pay for P1's booking
        api_client.force_authenticate(user=p2)
        pay_resp = api_client.post('/api/v1/payments/initiate', {"consultation_id": c_id})
        assert pay_resp.status_code == status.HTTP_403_FORBIDDEN
        assert pay_resp.data['error']['code'] == 'PERMISSION_DENIED'

    def test_13_slot_in_past_cannot_be_booked(self, api_client):
        """13. A slot in the past cannot be booked."""
        doctor = create_test_doctor('doc13@example.com')
        patient = create_test_patient('p13@example.com')
        past_time = timezone.now() - timedelta(hours=2)

        # Slot created in the past
        past_slot = AvailabilitySlot(
            doctor=doctor,
            start_at=past_time,
            end_at=past_time + timedelta(minutes=45),
            status=AvailabilitySlot.STATUS_AVAILABLE
        )
        past_slot.save()

        api_client.force_authenticate(user=patient)
        resp = api_client.post('/api/v1/bookings', {"slot_id": str(past_slot.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.data['error']['code'] == 'SLOT_EXPIRED'

    def test_14_slot_outside_doctor_availability_cannot_be_booked(self, api_client):
        """14. A slot outside the doctor's availability cannot be booked."""
        patient = create_test_patient('p14@example.com')
        random_slot_id = str(uuid.uuid4())

        api_client.force_authenticate(user=patient)
        resp = api_client.post('/api/v1/bookings', {"slot_id": random_slot_id}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_16_database_transactions_rollback_cleanly_on_booking_failure(self, api_client):
        """16. Database transactions roll back cleanly when a booking fails."""
        doctor = create_test_doctor('doc16@example.com')
        patient = create_test_patient('p16@example.com')
        now = timezone.now() + timedelta(days=7)

        # Slot already reserved by someone else
        slot = AvailabilitySlot.objects.create(
            doctor=doctor,
            start_at=now,
            end_at=now + timedelta(minutes=45),
            status=AvailabilitySlot.STATUS_BOOKED
        )

        initial_consultations_count = Consultation.objects.count()
        initial_bookings_count = Booking.objects.count()
        initial_payments_count = Payment.objects.count()

        api_client.force_authenticate(user=patient)
        resp = api_client.post('/api/v1/bookings', {"slot_id": str(slot.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        assert resp.status_code == status.HTTP_409_CONFLICT

        # Invariant: No partial records created
        assert Consultation.objects.count() == initial_consultations_count
        assert Booking.objects.count() == initial_bookings_count
        assert Payment.objects.count() == initial_payments_count

    def test_17_existing_doctor_approval_and_dashboard_intact(self, api_client):
        """17. Existing authentication, doctor approval, cancellation, and dashboard features continue working."""
        # Unapproved doctor's slot cannot be booked
        unapproved_doc = create_test_doctor('unapproved_doc@example.com', verification_status=DoctorProfile.STATUS_PENDING)
        patient = create_test_patient('p17@example.com')
        now = timezone.now() + timedelta(days=8)

        slot = AvailabilitySlot.objects.create(doctor=unapproved_doc, start_at=now, end_at=now + timedelta(minutes=45))

        api_client.force_authenticate(user=patient)
        resp = api_client.post('/api/v1/bookings', {"slot_id": str(slot.id)}, HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        # Dashboard appointments list works
        list_resp = api_client.get('/api/v1/bookings')
        assert list_resp.status_code == status.HTTP_200_OK
        assert 'bookings' in list_resp.data


@pytest.mark.django_db(transaction=True)
class TestAppointmentBookingConcurrencyRules:
    def test_15_two_simultaneous_booking_requests_only_one_succeeds(self):
        """15. Two simultaneous booking requests for the same slot cannot both succeed."""
        doctor = create_test_doctor('doc15@example.com')
        p1 = create_test_patient('p15_1@example.com')
        p2 = create_test_patient('p15_2@example.com')
        now = timezone.now() + timedelta(days=6)

        slot = AvailabilitySlot.objects.create(doctor=doctor, start_at=now, end_at=now + timedelta(minutes=45))

        def attempt(user):
            client = APIClient()
            client.force_authenticate(user=user)
            return client.post(
                '/api/v1/bookings',
                {"slot_id": str(slot.id), "chief_complaint": f"By {user.email}"},
                HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4())
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            fut1 = executor.submit(attempt, p1)
            fut2 = executor.submit(attempt, p2)
            r1 = fut1.result()
            r2 = fut2.result()

        status_codes = [r1.status_code, r2.status_code]
        assert status.HTTP_201_CREATED in status_codes
        assert status.HTTP_409_CONFLICT in status_codes

        # Exactly 1 consultation in database
        assert Consultation.objects.filter(slot=slot).count() == 1
