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
        user = serializer.save()

        log_audit_event(
            action='AUTH_REGISTER',
            resource_type='USER',
            resource_id=str(user.id),
            actor=user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS,
            metadata={'email': user.email, 'role': user.role}
        )

        return Response(
            {
                "success": True,
                "message": "Registration successful. You can now log in.",
                "user": UserSerializer(user).data
            },
            status=status.HTTP_201_CREATED
        )

class LoginView(TokenObtainPairView):
    """
    Authenticates user with email and password, returning JWT access & refresh tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(summary="User login (JWT)")
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            log_audit_event(
                action='AUTH_LOGIN',
                resource_type='USER',
                resource_id=str(user.id),
                actor=user,
                request=request,
                outcome=AuditLog.OUTCOME_SUCCESS,
                metadata={'email': user.email, 'role': user.role}
            )
            return Response({
                "success": True,
                "access": serializer.validated_data.get('access'),
                "refresh": serializer.validated_data.get('refresh'),
                "user": serializer.validated_data.get('user')
            }, status=status.HTTP_200_OK)
        except Exception as e:
            log_audit_event(
                action='AUTH_LOGIN_FAILED',
                resource_type='USER',
                request=request,
                outcome=AuditLog.OUTCOME_FAILURE,
                metadata={'attempted_email': request.data.get('email', '')}
            )
            raise e

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
