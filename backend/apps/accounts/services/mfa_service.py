import io
import uuid
import base64
import hashlib
import secrets
from datetime import timedelta
import pyotp
import qrcode
from cryptography.fernet import Fernet
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from apps.accounts.models import User, UserMFA, MFARecoveryCode, MFAChallenge
from apps.audit.utils import log_audit_event
from apps.audit.models import AuditLog


def get_fernet() -> Fernet:
    """
    Returns a Fernet symmetric cipher instance.
    Uses MFA_ENCRYPTION_KEY if provided in settings, otherwise derives
    a deterministic 32-byte urlsafe base64 key from Django SECRET_KEY.
    """
    raw_key = getattr(settings, 'MFA_ENCRYPTION_KEY', None)
    if raw_key:
        if isinstance(raw_key, str):
            raw_key = raw_key.encode('utf-8')
        return Fernet(raw_key)
    
    # Deterministic SHA-256 derivation from SECRET_KEY
    derived = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    urlsafe_key = base64.urlsafe_b64encode(derived)
    return Fernet(urlsafe_key)


def encrypt_secret(plain_secret: str) -> str:
    f = get_fernet()
    return f.encrypt(plain_secret.encode('utf-8')).decode('utf-8')


def decrypt_secret(encrypted_secret: str) -> str:
    f = get_fernet()
    return f.decrypt(encrypted_secret.encode('utf-8')).decode('utf-8')


class MFAService:
    """
    Service Layer: Encapsulates all Multi-Factor Authentication logic including
    TOTP secret generation, QR code formatting, challenge/verification workflows,
    and single-use recovery code management.
    """

    @staticmethod
    def setup_mfa(user: User) -> dict:
        """
        Initiates MFA enrollment by generating an RFC 6238 TOTP secret,
        saving it encrypted in UserMFA with is_enabled=False, and returning
        the provisioning URI and a Base64 QR code image.
        """
        secret = pyotp.random_base32()
        encrypted = encrypt_secret(secret)

        user_mfa, _ = UserMFA.objects.update_or_create(
            user=user,
            defaults={
                'encrypted_secret': encrypted,
                'is_enabled': False,
            }
        )

        issuer = getattr(settings, 'MFA_ISSUER_NAME', 'Amrutam Telemedicine')
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name=issuer)

        # Generate QR code as PNG in memory
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#2B5B41", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        qr_data_uri = f"data:image/png;base64,{qr_b64}"

        return {
            "secret": secret,
            "otpauth_url": provisioning_uri,
            "qr_code": qr_data_uri,
            "message": "Scan the QR code with your authenticator application, then submit a 6-digit verification code to activate MFA."
        }

    @staticmethod
    def confirm_mfa(user: User, code: str, request=None) -> dict:
        """
        Confirms MFA enrollment by verifying the initial 6-digit TOTP code.
        Upon success, activates MFA, generates 8 hashed single-use recovery codes,
        and logs the audit event.
        """
        try:
            user_mfa = UserMFA.objects.get(user=user)
        except UserMFA.DoesNotExist:
            raise ValidationError("MFA enrollment has not been initiated. Please call setup first.")

        plain_secret = decrypt_secret(user_mfa.encrypted_secret)
        totp = pyotp.TOTP(plain_secret)

        # Validate with +/- 30s drift window
        if not totp.verify(code.strip(), valid_window=1):
            log_audit_event(
                action='AUTH_MFA_ENROLL_FAILED',
                resource_type='USER',
                resource_id=str(user.id),
                actor=user,
                request=request,
                outcome=AuditLog.OUTCOME_FAILURE,
                metadata={'reason': 'Invalid confirmation code'}
            )
            raise ValidationError({"code": "Invalid verification code. Please check your authenticator app and try again."})

        # Mark MFA enabled
        now = timezone.now()
        user_mfa.is_enabled = True
        user_mfa.enabled_at = now
        user_mfa.last_used_at = now
        user_mfa.save()

        # Delete any previous recovery codes and generate 8 new single-use codes
        user.mfa_recovery_codes.all().delete()
        plain_recovery_codes = []
        recovery_objects = []

        for _ in range(8):
            code_part1 = secrets.token_hex(2).upper()
            code_part2 = secrets.token_hex(2).upper()
            plain_code = f"{code_part1}-{code_part2}"
            plain_recovery_codes.append(plain_code)
            
            hashed = make_password(plain_code)
            recovery_objects.append(
                MFARecoveryCode(
                    user=user,
                    hashed_code=hashed,
                    is_used=False
                )
            )

        MFARecoveryCode.objects.bulk_create(recovery_objects)

        log_audit_event(
            action='AUTH_MFA_ENROLLED',
            resource_type='USER',
            resource_id=str(user.id),
            actor=user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS,
            metadata={'recovery_codes_generated': 8}
        )

        return {
            "success": True,
            "message": "Two-factor authentication has been successfully activated.",
            "recovery_codes": plain_recovery_codes,
            "notice": "Store these recovery codes in a secure place. Each code can only be used once if you lose access to your authenticator device."
        }

    @staticmethod
    def create_mfa_challenge(user: User) -> str:
        """
        Creates an ephemeral, restricted challenge token valid for 5 minutes.
        """
        timeout_minutes = getattr(settings, 'MFA_CHALLENGE_TIMEOUT_MINUTES', 5)
        expires_at = timezone.now() + timedelta(minutes=timeout_minutes)
        token = f"mfa_{secrets.token_urlsafe(32)}"

        MFAChallenge.objects.create(
            user=user,
            token=token,
            expires_at=expires_at,
            is_used=False
        )
        return token

    @staticmethod
    def verify_mfa_login(challenge_token: str, code: str, request=None) -> tuple[User, dict]:
        """
        Verifies the second factor during the login process using either a 6-digit TOTP
        code or an unused single-use recovery code.
        """
        if not challenge_token or not code:
            raise ValidationError("Both challenge token and verification code are required.")

        now = timezone.now()
        try:
            challenge = MFAChallenge.objects.select_related('user').get(
                token=challenge_token,
                is_used=False,
                expires_at__gt=now
            )
        except MFAChallenge.DoesNotExist:
            raise ValidationError("The MFA challenge token is invalid or has expired. Please sign in again.")

        user = challenge.user
        clean_code = code.strip().upper()
        verified = False
        used_recovery = False

        # 1. Try TOTP verification if digits
        clean_digits = clean_code.replace(" ", "").replace("-", "")
        if clean_digits.isdigit() and len(clean_digits) == 6:
            try:
                user_mfa = UserMFA.objects.get(user=user, is_enabled=True)
                plain_secret = decrypt_secret(user_mfa.encrypted_secret)
                totp = pyotp.TOTP(plain_secret)
                if totp.verify(clean_digits, valid_window=1):
                    verified = True
                    user_mfa.last_used_at = now
                    user_mfa.save(update_fields=['last_used_at'])
            except UserMFA.DoesNotExist:
                pass

        # 2. Try single-use recovery code if not verified via TOTP
        if not verified:
            unused_codes = user.mfa_recovery_codes.filter(is_used=False)
            for rec in unused_codes:
                if check_password(clean_code, rec.hashed_code):
                    rec.is_used = True
                    rec.used_at = now
                    rec.save(update_fields=['is_used', 'used_at'])
                    verified = True
                    used_recovery = True
                    break

        if not verified:
            log_audit_event(
                action='AUTH_MFA_FAILED',
                resource_type='USER',
                resource_id=str(user.id),
                actor=user,
                request=request,
                outcome=AuditLog.OUTCOME_FAILURE,
                metadata={'reason': 'Invalid code or recovery code'}
            )
            raise ValidationError("Invalid verification or recovery code.")

        # Invalidate challenge token
        challenge.is_used = True
        challenge.save(update_fields=['is_used'])

        # Issue full JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        from apps.accounts.serializers import UserSerializer

        refresh = RefreshToken.for_user(user)
        refresh['email'] = user.email
        refresh['role'] = user.role
        refresh['full_name'] = user.full_name

        tokens = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data
        }

        log_audit_event(
            action='AUTH_MFA_SUCCESS',
            resource_type='USER',
            resource_id=str(user.id),
            actor=user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS,
            metadata={'used_recovery': used_recovery}
        )

        return user, tokens

    @staticmethod
    def disable_mfa(user: User, password: str, code: str, request=None) -> dict:
        """
        Disables MFA after re-verifying password and a valid TOTP code.
        """
        if not user.check_password(password):
            raise ValidationError({"password": "Incorrect password."})

        try:
            user_mfa = UserMFA.objects.get(user=user, is_enabled=True)
        except UserMFA.DoesNotExist:
            raise ValidationError("MFA is not currently active on this account.")

        plain_secret = decrypt_secret(user_mfa.encrypted_secret)
        totp = pyotp.TOTP(plain_secret)
        clean_code = code.strip().replace(" ", "").replace("-", "")

        if not totp.verify(clean_code, valid_window=1):
            raise ValidationError({"code": "Invalid authenticator code. MFA could not be disabled."})

        user_mfa.is_enabled = False
        user_mfa.save(update_fields=['is_enabled'])
        user.mfa_recovery_codes.all().delete()

        log_audit_event(
            action='AUTH_MFA_DISABLED',
            resource_type='USER',
            resource_id=str(user.id),
            actor=user,
            request=request,
            outcome=AuditLog.OUTCOME_SUCCESS
        )

        return {"success": True, "message": "Two-factor authentication has been disabled."}

    @staticmethod
    def get_mfa_status(user: User) -> dict:
        is_enabled = False
        if hasattr(user, 'mfa_settings'):
            is_enabled = user.mfa_settings.is_enabled

        return {
            "success": True,
            "mfa_enabled": is_enabled,
            "is_enabled": is_enabled,
            "mfa_required": user.role == User.ROLE_ADMIN,
            "has_recovery_codes": user.mfa_recovery_codes.filter(is_used=False).count() if is_enabled else 0
        }
