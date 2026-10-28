import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be provided.')
        email = self.normalize_email(email).lower()
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.ROLE_ADMIN)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_PATIENT = 'PATIENT'
    ROLE_DOCTOR = 'DOCTOR'
    ROLE_ADMIN = 'ADMIN'

    ROLE_CHOICES = (
        (ROLE_PATIENT, 'Patient'),
        (ROLE_DOCTOR, 'Doctor'),
        (ROLE_ADMIN, 'Administrator'),
    )

    STATUS_ACTIVE = 'ACTIVE'
    STATUS_SUSPENDED = 'SUSPENDED'
    STATUS_DEACTIVATED = 'DEACTIVATED'

    STATUS_CHOICES = (
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_DEACTIVATED, 'Deactivated'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_PATIENT, db_index=True)
    account_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.email} ({self.role})"

class PatientProfile(models.Model):
    GENDER_MALE = 'MALE'
    GENDER_FEMALE = 'FEMALE'
    GENDER_OTHER = 'OTHER'
    GENDER_PREFER_NOT_TO_SAY = 'PREFER_NOT_TO_SAY'

    GENDER_CHOICES = (
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
        (GENDER_OTHER, 'Other'),
        (GENDER_PREFER_NOT_TO_SAY, 'Prefer not to say'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=25, choices=GENDER_CHOICES, default=GENDER_PREFER_NOT_TO_SAY)
    blood_group = models.CharField(max_length=10, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    medical_history_summary = models.TextField(blank=True, null=True, help_text="Synthetic patient history")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Patient Profile: {self.user.email}"


class UserMFA(models.Model):
    """
    Stores TOTP-based Multi-Factor Authentication configuration.
    The TOTP base32 secret is encrypted at rest using application-level Fernet encryption.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mfa_settings')
    encrypted_secret = models.TextField(help_text="Fernet-encrypted TOTP base32 secret")
    is_enabled = models.BooleanField(default=False, db_index=True)
    enabled_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User MFA Settings'
        verbose_name_plural = 'User MFA Settings'

    def __str__(self):
        return f"MFA ({'Enabled' if self.is_enabled else 'Disabled'}) for {self.user.email}"


class MFARecoveryCode(models.Model):
    """
    Stores single-use hashed recovery backup codes for MFA accounts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mfa_recovery_codes')
    hashed_code = models.CharField(max_length=128)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'MFA Recovery Code'
        verbose_name_plural = 'MFA Recovery Codes'
        indexes = [
            models.Index(fields=['user', 'is_used']),
        ]

    def __str__(self):
        return f"Recovery Code ({'Used' if self.is_used else 'Available'}) for {self.user.email}"


class MFAChallenge(models.Model):
    """
    Tracks ephemeral, short-lived MFA login challenge tokens.
    Does not grant API access; valid only for second-factor verification.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mfa_challenges')
    token = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'MFA Challenge'
        verbose_name_plural = 'MFA Challenges'
        indexes = [
            models.Index(fields=['token', 'is_used', 'expires_at']),
        ]

    def __str__(self):
        return f"MFA Challenge for {self.user.email} (expires {self.expires_at})"
