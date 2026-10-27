import pytest
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
class TestAuthenticationAPI:
    def test_patient_registration_success(self, api_client):
        payload = {
            "email": "newpatient@example.com",
            "first_name": "Kavya",
            "last_name": "Rao",
            "phone_number": "+919988776655",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!"
        }
        response = api_client.post('/api/v1/auth/register', payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['user']['email'] == 'newpatient@example.com'
        assert response.data['user']['role'] == 'PATIENT'

        # Verify in DB
        user = User.objects.get(email='newpatient@example.com')
        assert user.role == User.ROLE_PATIENT
        assert user.check_password('StrongPassword123!')

    def test_public_registration_cannot_escalate_to_admin(self, api_client):
        payload = {
            "email": "hacker@example.com",
            "first_name": "Malicious",
            "last_name": "User",
            "role": "ADMIN",  # Attempting privilege escalation
            "password": "HackerPassword123!",
            "password_confirm": "HackerPassword123!"
        }
        response = api_client.post('/api/v1/auth/register', payload)
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email='hacker@example.com')
        # Role must still be PATIENT
        assert user.role == User.ROLE_PATIENT

    def test_login_and_jwt_issuance(self, api_client):
        User.objects.create_user(
            email='loginuser@example.com',
            password='ValidPassword123!',
            first_name='Rohan',
            last_name='Das'
        )
        response = api_client.post('/api/v1/auth/login', {
            'email': 'loginuser@example.com',
            'password': 'ValidPassword123!'
        })
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['user']['email'] == 'loginuser@example.com'

    def test_login_invalid_password_fails(self, api_client):
        User.objects.create_user(
            email='loginuser2@example.com',
            password='ValidPassword123!'
        )
        response = api_client.post('/api/v1/auth/login', {
            'email': 'loginuser2@example.com',
            'password': 'WrongPassword!'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh_and_rotation(self, api_client):
        user = User.objects.create_user(
            email='refreshuser@example.com',
            password='ValidPassword123!'
        )
        login_resp = api_client.post('/api/v1/auth/login', {
            'email': 'refreshuser@example.com',
            'password': 'ValidPassword123!'
        })
        refresh_token = login_resp.data['refresh']

        # Refresh
        refresh_resp = api_client.post('/api/v1/auth/refresh', {'refresh': refresh_token})
        assert refresh_resp.status_code == status.HTTP_200_OK
        assert 'access' in refresh_resp.data
        new_refresh = refresh_resp.data.get('refresh')
        assert new_refresh is not None

    def test_logout_blacklists_token(self, api_client):
        user = User.objects.create_user(
            email='logoutuser@example.com',
            password='ValidPassword123!'
        )
        login_resp = api_client.post('/api/v1/auth/login', {
            'email': 'logoutuser@example.com',
            'password': 'ValidPassword123!'
        })
        access_token = login_resp.data['access']
        refresh_token = login_resp.data['refresh']

        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_resp = api_client.post('/api/v1/auth/logout', {'refresh': refresh_token})
        assert logout_resp.status_code == status.HTTP_200_OK

        # Attempt to use blacklisted refresh token
        retry_refresh = api_client.post('/api/v1/auth/refresh', {'refresh': refresh_token})
        assert retry_refresh.status_code == status.HTTP_401_UNAUTHORIZED
