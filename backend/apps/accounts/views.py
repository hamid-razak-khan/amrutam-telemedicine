from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from apps.accounts.models import User
from apps.accounts.serializers import (
    UserRegisterSerializer,
    UserSerializer,
    UserProfileUpdateSerializer,
    CustomTokenObtainPairSerializer,
)
from apps.audit.utils import log_audit_event
from apps.audit.models import AuditLog

from apps.accounts.services.auth_service import AuthService
from apps.accounts.services.mfa_service import MFAService
from apps.accounts.serializers import (
    UserRegisterSerializer,
    UserSerializer,
    UserProfileUpdateSerializer,
    CustomTokenObtainPairSerializer,
    MFAConfirmSerializer,
    MFAVerifyLoginSerializer,
    MFADisableSerializer,
)

class RegisterView(generics.CreateAPIView):
    """
    Public registration endpoint. Exclusively creates accounts with the PATIENT role.
    Privileged DOCTOR or ADMIN roles cannot be self-assigned.
    """
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(summary="Patient self-registration", responses={201: UserSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService.register_patient(serializer.validated_data, request=request)

        return Response(
            {
                "success": True,
                "message": "Registration successful. You can now log in.",
                "user": UserSerializer(user).data
            },
            status=status.HTTP_201_CREATED
        )

class LoginView(APIView):
    """
    Authenticates user with email and password.
    Enforces active status, doctor approval status, and TOTP-based MFA challenges.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(summary="User login with MFA challenge support")
    def post(self, request, *args, **kwargs):
        email = request.data.get('email', '')
        password = request.data.get('password', '')
        result = AuthService.authenticate_user(email, password, request=request)
        return Response(result, status=status.HTTP_200_OK)

class MFASetupView(APIView):
    """Initiates MFA enrollment by generating a TOTP secret and QR code."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Generate TOTP MFA enrollment QR code and secret")
    def post(self, request):
        result = MFAService.setup_mfa(request.user)
        return Response(result, status=status.HTTP_200_OK)

class MFAConfirmView(APIView):
    """Confirms MFA enrollment with 6-digit TOTP code and generates single-use recovery codes."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Confirm MFA enrollment and activate 2FA")
    def post(self, request):
        serializer = MFAConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = MFAService.confirm_mfa(request.user, serializer.validated_data['code'], request=request)
        return Response(result, status=status.HTTP_200_OK)

class MFAVerifyLoginView(APIView):
    """Completes step 2 of login using challenge token + 6-digit TOTP or backup recovery code."""
    permission_classes = [permissions.AllowAny]

    @extend_schema(summary="Verify MFA login challenge and issue JWT tokens")
    def post(self, request):
        serializer = MFAVerifyLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, tokens = MFAService.verify_mfa_login(
            serializer.validated_data['mfa_token'],
            serializer.validated_data['code'],
            request=request
        )
        return Response({
            "success": True,
            "access": tokens['access'],
            "refresh": tokens['refresh'],
            "user": tokens['user']
        }, status=status.HTTP_200_OK)

class MFADisableView(APIView):
    """Disables MFA after validating password and current TOTP code."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Disable two-factor authentication")
    def post(self, request):
        serializer = MFADisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = MFAService.disable_mfa(
            request.user,
            serializer.validated_data['password'],
            serializer.validated_data['code'],
            request=request
        )
        return Response(result, status=status.HTTP_200_OK)

class MFAStatusView(APIView):
    """Checks the MFA status and requirement for the authenticated user."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Check MFA status for current user")
    def get(self, request):
        result = MFAService.get_mfa_status(request.user)
        return Response(result, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Logs out the user by blacklisting their refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="User logout and token revocation")
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {"success": False, "error": {"code": "VALIDATION_ERROR", "message": "Refresh token is required."}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()

            log_audit_event(
                action='AUTH_LOGOUT',
                resource_type='USER',
                resource_id=str(request.user.id),
                actor=request.user,
                request=request,
                outcome=AuditLog.OUTCOME_SUCCESS
            )
            return Response({"success": True, "message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"success": False, "error": {"code": "INVALID_TOKEN", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST
            )

class CurrentUserView(APIView):
    """
    Returns the currently authenticated user's profile and permissions.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="Current authenticated user details", responses={200: UserSerializer})
    def get(self, request):
        serializer = UserSerializer(request.user)
        data = serializer.data
        if request.user.role == User.ROLE_DOCTOR and hasattr(request.user, 'doctor_profile'):
            from apps.doctors.serializers import DoctorProfileSerializer
            data['doctor_profile'] = DoctorProfileSerializer(request.user.doctor_profile).data
        return Response({"success": True, "user": data}, status=status.HTTP_200_OK)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieves or updates permitted profile information for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileUpdateSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserSerializer

    @extend_schema(summary="Retrieve user profile")
    def get(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserSerializer(user)
        return Response({"success": True, "user": serializer.data})

    @extend_schema(summary="Update user profile")
    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        log_audit_event(
            action='PROFILE_UPDATED',
            resource_type='USER',
            resource_id=str(user.id),
            actor=user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS
        )

        return Response({"success": True, "user": UserSerializer(user).data})
