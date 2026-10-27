import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.doctors.models import DoctorProfile
from apps.availability.models import AvailabilitySlot
from apps.consultations.models import Consultation

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
class TestSecurityAndRBAC:
    def test_patient_cannot_access_other_patient_booking(self, api_client):
        # Patient A & B
        patient_a = User.objects.create_user(email='patient_a@example.com', password='Password123!', role=User.ROLE_PATIENT)
        patient_b = User.objects.create_user(email='patient_b@example.com', password='Password123!', role=User.ROLE_PATIENT)

        doc_user = User.objects.create_user(email='doc_sec@example.com', password='Password123!', role=User.ROLE_DOCTOR)
        doc = DoctorProfile.objects.create(user=doc_user, specialization='Ayurveda')

        now = timezone.now() + timedelta(days=1)
        slot = AvailabilitySlot.objects.create(doctor=doc, start_at=now, end_at=now + timedelta(minutes=45))

        # Booking for Patient B
        consultation = Consultation.objects.create(
            booking_reference='AMR-PATIENT-B',
            patient=patient_b,
            doctor=doc,
            slot=slot,
            scheduled_start=slot.start_at,
            scheduled_end=slot.end_at,
            status=Consultation.STATUS_BOOKED
        )

        # Authenticate as Patient A
        api_client.force_authenticate(user=patient_a)

        # Patient A attempts to retrieve Patient B's booking
        resp = api_client.get(f'/api/v1/bookings/{consultation.id}')
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert 'PERMISSION_DENIED' in resp.data['error']['code']

    def test_patient_cannot_call_doctor_endpoints(self, api_client):
        patient = User.objects.create_user(email='patient_calls_doc@example.com', password='Password123!', role=User.ROLE_PATIENT)
        api_client.force_authenticate(user=patient)

        # Patient tries to post availability slot
        resp = api_client.post('/api/v1/doctors/me/availability', {
            'start_at': (timezone.now() + timedelta(days=1)).isoformat(),
            'end_at': (timezone.now() + timedelta(days=1, hours=1)).isoformat()
        })
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_doctor_cannot_manage_unrelated_consultations(self, api_client):
        doc1_user = User.objects.create_user(email='doc1_perm@example.com', password='Password123!', role=User.ROLE_DOCTOR)
        doc1 = DoctorProfile.objects.create(user=doc1_user, specialization='Ayurveda')

        doc2_user = User.objects.create_user(email='doc2_perm@example.com', password='Password123!', role=User.ROLE_DOCTOR)
        doc2 = DoctorProfile.objects.create(user=doc2_user, specialization='Ayurveda')

        patient = User.objects.create_user(email='patient_perm@example.com', password='Password123!')
        now = timezone.now() + timedelta(days=1)
        slot = AvailabilitySlot.objects.create(doctor=doc1, start_at=now, end_at=now + timedelta(minutes=45))

        # Consultation assigned to Doctor 1
        consultation = Consultation.objects.create(
            booking_reference='AMR-DOC1-ONLY',
            patient=patient,
            doctor=doc1,
            slot=slot,
            scheduled_start=slot.start_at,
            scheduled_end=slot.end_at,
            status=Consultation.STATUS_BOOKED
        )

        # Authenticate as Doctor 2
        api_client.force_authenticate(user=doc2_user)

        # Doctor 2 attempts to start Doctor 1's consultation
        resp = api_client.post(f'/api/v1/consultations/{consultation.id}/start')
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.data['error']['code'] == 'PERMISSION_DENIED'

    def test_patient_cannot_access_admin_analytics(self, api_client):
        patient = User.objects.create_user(email='patient_noadmin@example.com', password='Password123!', role=User.ROLE_PATIENT)
        api_client.force_authenticate(user=patient)

        resp = api_client.get('/api/v1/admin/analytics/overview')
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_access_admin_analytics_and_audit(self, api_client):
        admin = User.objects.create_user(email='admin_perm@example.com', password='Password123!', role=User.ROLE_ADMIN)
        api_client.force_authenticate(user=admin)

        resp = api_client.get('/api/v1/admin/analytics/overview')
        assert resp.status_code == status.HTTP_200_OK
        assert 'metrics' in resp.data

        audit_resp = api_client.get('/api/v1/admin/audit-logs')
        assert audit_resp.status_code == status.HTTP_200_OK
