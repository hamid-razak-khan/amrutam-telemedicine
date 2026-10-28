import pytest
import pyotp
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, UserMFA, MFARecoveryCode
from apps.doctors.models import DoctorProfile
from apps.availability.models import AvailabilitySlot

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
class TestDoctorApprovalAndMFA:
    def test_doctor_registration_creates_pending_status(self, api_client):
        payload = {
            "email": "dr.ayush.test@example.com",
            "first_name": "Siddharth",
            "last_name": "Sharma",
            "phone_number": "+919876543210",
            "password": "DoctorPassword123!",
            "password_confirm": "DoctorPassword123!",
            "license_number": "AYUSH-KA-2024-9988",
            "specialization": "Ayurveda Panchakarma",
            "credentials": "BAMS, MD (Ayurveda), RGUHS",
            "years_of_experience": 8,
            "consultation_fee": "850.00",
            "biography": "Senior practitioner in Ayurvedic rejuvenation therapies."
        }
        resp = api_client.post('/api/v1/auth/register-doctor', payload)
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data['success'] is True
        assert resp.data['doctor']['verification_status'] == 'PENDING'
        assert resp.data['doctor']['license_number'] == 'AYUSH-KA-2024-9988'

        user = User.objects.get(email='dr.ayush.test@example.com')
        assert user.role == User.ROLE_DOCTOR
        doc_profile = DoctorProfile.objects.get(user=user)
        assert doc_profile.verification_status == DoctorProfile.STATUS_PENDING

    def test_doctor_login_blocked_while_pending_and_approved_lifecycle(self, api_client):
        # 1. Register a pending doctor
        doc_user = User.objects.create_user(
            email='dr.pending@example.com',
            password='DocPassword123!',
            first_name='Ananya',
            last_name='Nair',
            role=User.ROLE_DOCTOR
        )
        doc_profile = DoctorProfile.objects.create(
            user=doc_user,
            license_number='AYUSH-KL-1234',
            specialization='Ayurveda',
            verification_status=DoctorProfile.STATUS_PENDING
        )

        # 2. Attempt login while PENDING -> Expect HTTP 403
        resp_login = api_client.post('/api/v1/auth/login', {
            'email': 'dr.pending@example.com',
            'password': 'DocPassword123!'
        })
        assert resp_login.status_code == status.HTTP_403_FORBIDDEN
        assert resp_login.data['error']['code'] == 'DOCTOR_APPROVAL_PENDING'

        # 3. Create Admin and approve the doctor
        admin_user = User.objects.create_user(
            email='admin.approver@example.com',
            password='AdminPassword123!',
            role=User.ROLE_ADMIN
        )
        api_client.force_authenticate(user=admin_user)
        resp_approve = api_client.post(f'/api/v1/admin/doctors/{doc_profile.id}/approve')
        assert resp_approve.status_code == status.HTTP_200_OK
        assert resp_approve.data['doctor']['verification_status'] == 'APPROVED'

        # 4. Attempt login now that doctor is APPROVED -> Expect HTTP 200 with tokens
        api_client.force_authenticate(user=None)
        resp_login_success = api_client.post('/api/v1/auth/login', {
            'email': 'dr.pending@example.com',
            'password': 'DocPassword123!'
        })
        assert resp_login_success.status_code == status.HTTP_200_OK
        assert 'access' in resp_login_success.data

    def test_admin_rejects_doctor_with_reason(self, api_client):
        doc_user = User.objects.create_user(
            email='dr.rejected@example.com',
            password='DocPassword123!',
            role=User.ROLE_DOCTOR
        )
        doc_profile = DoctorProfile.objects.create(
            user=doc_user,
            license_number='FAKE-LICENSE-000',
            specialization='Ayurveda',
            verification_status=DoctorProfile.STATUS_PENDING
        )

        admin_user = User.objects.create_user(
            email='admin.rejector@example.com',
            password='AdminPassword123!',
            role=User.ROLE_ADMIN
        )
        api_client.force_authenticate(user=admin_user)
        resp_reject = api_client.post(
            f'/api/v1/admin/doctors/{doc_profile.id}/reject',
            {'reason': 'Medical council registration could not be verified in state registry.'}
        )
        assert resp_reject.status_code == status.HTTP_200_OK
        assert resp_reject.data['doctor']['verification_status'] == 'REJECTED'

        # Attempting login as rejected doctor -> HTTP 403 DOCTOR_APPROVAL_REJECTED
        api_client.force_authenticate(user=None)
        resp_login = api_client.post('/api/v1/auth/login', {
            'email': 'dr.rejected@example.com',
            'password': 'DocPassword123!'
        })
        assert resp_login.status_code == status.HTTP_403_FORBIDDEN
        assert resp_login.data['error']['code'] == 'DOCTOR_APPROVAL_REJECTED'
        assert 'Medical council registration' in resp_login.data['error']['message']

    def test_totp_mfa_setup_confirmation_and_login_challenge(self, api_client):
        # 1. Create a patient
        patient = User.objects.create_user(
            email='mfa.patient@example.com',
            password='PatientPassword123!',
            role=User.ROLE_PATIENT
        )
        api_client.force_authenticate(user=patient)

        # 2. Check initial MFA status
        status_resp = api_client.get('/api/v1/auth/mfa/status')
        assert status_resp.status_code == status.HTTP_200_OK
        assert status_resp.data['mfa_enabled'] is False

        # 3. Setup MFA
        setup_resp = api_client.post('/api/v1/auth/mfa/setup')
        assert setup_resp.status_code == status.HTTP_200_OK
        secret = setup_resp.data['secret']
        assert setup_resp.data['qr_code'].startswith('data:image/png;base64,')

        # 4. Confirm MFA with TOTP code
        totp = pyotp.TOTP(secret)
        current_code = totp.now()

        confirm_resp = api_client.post('/api/v1/auth/mfa/confirm', {'code': current_code})
        assert confirm_resp.status_code == status.HTTP_200_OK
        recovery_codes = confirm_resp.data['recovery_codes']
        assert len(recovery_codes) == 8

        # 5. Logout and log in with password -> MFA challenge should be returned
        api_client.force_authenticate(user=None)
        login_resp = api_client.post('/api/v1/auth/login', {
            'email': 'mfa.patient@example.com',
            'password': 'PatientPassword123!'
        })
        assert login_resp.status_code == status.HTTP_200_OK
        assert login_resp.data['mfa_required'] is True
        challenge_token = login_resp.data['mfa_token']

        # 6. Verify MFA challenge with TOTP code
        verify_resp = api_client.post('/api/v1/auth/mfa/verify', {
            'mfa_token': challenge_token,
            'code': totp.now()
        })
        assert verify_resp.status_code == status.HTTP_200_OK
        assert 'access' in verify_resp.data
        assert 'refresh' in verify_resp.data

        # 7. Test single-use recovery code on another login
        login_resp2 = api_client.post('/api/v1/auth/login', {
            'email': 'mfa.patient@example.com',
            'password': 'PatientPassword123!'
        })
        challenge_token2 = login_resp2.data['mfa_token']
        first_recovery_code = recovery_codes[0]

        recovery_login_resp = api_client.post('/api/v1/auth/mfa/verify', {
            'mfa_token': challenge_token2,
            'code': first_recovery_code
        })
        assert recovery_login_resp.status_code == status.HTTP_200_OK

        # 8. Attempting to re-use the exact same recovery code must fail
        login_resp3 = api_client.post('/api/v1/auth/login', {
            'email': 'mfa.patient@example.com',
            'password': 'PatientPassword123!'
        })
        challenge_token3 = login_resp3.data['mfa_token']

        reuse_resp = api_client.post('/api/v1/auth/mfa/verify', {
            'mfa_token': challenge_token3,
            'code': first_recovery_code
        })
        assert reuse_resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_removes_approved_doctor_and_dates_are_tracked(self, api_client):
        """Verify removing an approved doctor tracks joining and removal dates, and deactivates doctor."""
        from apps.availability.models import AvailabilitySlot
        from datetime import timedelta
        from django.utils import timezone

        # 1. Create an approved doctor with future available slot
        doc_user = User.objects.create_user(
            email='dr.remove_test@example.com',
            password='DocPassword123!',
            first_name='Kavita',
            last_name='Menon',
            role=User.ROLE_DOCTOR
        )
        doc_profile = DoctorProfile.objects.create(
            user=doc_user,
            license_number='AYUSH-MH-9922',
            specialization='Panchakarma',
            verification_status=DoctorProfile.STATUS_APPROVED,
            active_status=True,
            approved_at=timezone.now() - timedelta(days=60)
        )
        slot_future = AvailabilitySlot.objects.create(
            doctor=doc_profile,
            start_at=timezone.now() + timedelta(days=5),
            end_at=timezone.now() + timedelta(days=5, minutes=45),
            status=AvailabilitySlot.STATUS_AVAILABLE
        )

        # 2. Admin removes doctor
        admin_user = User.objects.create_user(
            email='admin.remover@example.com',
            password='AdminPassword123!',
            role=User.ROLE_ADMIN
        )
        api_client.force_authenticate(user=admin_user)
        remove_resp = api_client.post(
            f'/api/v1/admin/doctors/{doc_profile.id}/remove',
            {'reason': 'Contract ended, doctor relocated abroad.'}
        )
        assert remove_resp.status_code == status.HTTP_200_OK
        data = remove_resp.data['doctor']
        assert data['verification_status'] == 'REMOVED'
        assert data['active_status'] is False
        assert data['joining_date'] is not None
        assert data['removed_at'] is not None
        assert data['removal_reason'] == 'Contract ended, doctor relocated abroad.'

        # 3. Check DB state
        doc_profile.refresh_from_db()
        assert doc_profile.verification_status == DoctorProfile.STATUS_REMOVED
        assert doc_profile.active_status is False
        assert doc_profile.removed_at is not None
        assert doc_profile.user.is_active is False

        # Future slot should be cancelled
        slot_future.refresh_from_db()
        assert slot_future.status == AvailabilitySlot.STATUS_CANCELLED

        # 4. Filter doctors list by REMOVED status
        list_resp = api_client.get('/api/v1/admin/doctors?status=REMOVED')
        assert list_resp.status_code == status.HTTP_200_OK
        removed_ids = [d['id'] for d in list_resp.data['doctors']]
        assert str(doc_profile.id) in removed_ids

        # 5. Admin restores doctor
        restore_resp = api_client.post(f'/api/v1/admin/doctors/{doc_profile.id}/approve')
        assert restore_resp.status_code == status.HTTP_200_OK
        assert restore_resp.data['doctor']['verification_status'] == 'APPROVED'
        assert restore_resp.data['doctor']['active_status'] is True

        doc_profile.refresh_from_db()
        assert doc_profile.verification_status == DoctorProfile.STATUS_APPROVED
        assert doc_profile.active_status is True
        assert doc_profile.user.is_active is True

