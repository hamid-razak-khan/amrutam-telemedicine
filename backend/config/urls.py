from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.common.views import HealthLiveView, HealthReadyView, RestrictedMetricsView
from apps.accounts.views import (
    RegisterView,
    LoginView,
    LogoutView,
    CurrentUserView,
    UserProfileView,
    MFASetupView,
    MFAConfirmView,
    MFAVerifyLoginView,
    MFADisableView,
    MFAStatusView,
)
from apps.doctors.views import (
    DoctorListView,
    DoctorDetailView,
    DoctorAvailabilityListView,
    DoctorProfileMeView,
    DoctorMyAvailabilityView,
    DoctorSlotDetailView,
    DoctorRegisterView,
    AdminDoctorApplicationsListView,
    AdminDoctorApproveView,
    AdminDoctorRejectView,
    AdminDoctorRemoveView,
)
from apps.bookings.views import (
    BookingListCreateView,
    BookingDetailView,
    BookingCancelView,
)
from apps.consultations.views import (
    ConsultationListView,
    ConsultationDetailView,
    ConsultationStartView,
    ConsultationCompleteView,
)
from apps.prescriptions.views import (
    PrescriptionListCreateForConsultationView,
    PrescriptionListView,
    PrescriptionDetailView,
)
from apps.payments.views import (
    PaymentInitiateView,
    PaymentDetailView,
)
from apps.analytics.views import (
    AdminAnalyticsOverviewView,
    AdminAnalyticsConsultationsView,
)
from apps.audit.views import (
    AdminAuditLogListView,
)

api_v1_patterns = [
    # Auth & Registration
    path('auth/register', RegisterView.as_view(), name='auth-register'),
    path('auth/register-doctor', DoctorRegisterView.as_view(), name='auth-register-doctor'),
    path('auth/login', LoginView.as_view(), name='auth-login'),
    path('auth/refresh', TokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/logout', LogoutView.as_view(), name='auth-logout'),
    path('auth/me', CurrentUserView.as_view(), name='auth-me'),

    # Multi-Factor Authentication (MFA)
    path('auth/mfa/setup', MFASetupView.as_view(), name='auth-mfa-setup'),
    path('auth/mfa/confirm', MFAConfirmView.as_view(), name='auth-mfa-confirm'),
    path('auth/mfa/verify', MFAVerifyLoginView.as_view(), name='auth-mfa-verify'),
    path('auth/mfa/verify-login', MFAVerifyLoginView.as_view(), name='auth-mfa-verify-login'),
    path('auth/mfa/disable', MFADisableView.as_view(), name='auth-mfa-disable'),
    path('auth/mfa/status', MFAStatusView.as_view(), name='auth-mfa-status'),

    # Users
    path('users/me', UserProfileView.as_view(), name='users-me'),


    # Doctors
    path('doctors', DoctorListView.as_view(), name='doctor-list'),
    path('doctors/<uuid:id>', DoctorDetailView.as_view(), name='doctor-detail'),
    path('doctors/<uuid:id>/availability', DoctorAvailabilityListView.as_view(), name='doctor-availability'),
    path('doctors/me/profile', DoctorProfileMeView.as_view(), name='doctor-profile-me'),
    path('doctors/me/availability', DoctorMyAvailabilityView.as_view(), name='doctor-availability-me'),
    path('doctors/me/availability/<uuid:slot_id>', DoctorSlotDetailView.as_view(), name='doctor-slot-detail'),

    # Bookings
    path('bookings', BookingListCreateView.as_view(), name='booking-list-create'),
    path('bookings/<uuid:id>', BookingDetailView.as_view(), name='booking-detail'),
    path('bookings/<uuid:id>/cancel', BookingCancelView.as_view(), name='booking-cancel'),

    # Consultations
    path('consultations', ConsultationListView.as_view(), name='consultation-list'),
    path('consultations/<uuid:id>', ConsultationDetailView.as_view(), name='consultation-detail'),
    path('consultations/<uuid:id>/start', ConsultationStartView.as_view(), name='consultation-start'),
    path('consultations/<uuid:id>/complete', ConsultationCompleteView.as_view(), name='consultation-complete'),

    # Prescriptions
    path('consultations/<uuid:id>/prescriptions', PrescriptionListCreateForConsultationView.as_view(), name='consultation-prescriptions'),
    path('prescriptions', PrescriptionListView.as_view(), name='prescription-list'),
    path('prescriptions/<uuid:id>', PrescriptionDetailView.as_view(), name='prescription-detail'),

    # Payments
    path('payments', PaymentInitiateView.as_view(), name='payment-initiate'),
    path('payments/initiate', PaymentInitiateView.as_view(), name='payment-initiate-alias'),
    path('payments/<uuid:id>', PaymentDetailView.as_view(), name='payment-detail'),

    # Administration
    path('admin/analytics/overview', AdminAnalyticsOverviewView.as_view(), name='admin-analytics-overview'),
    path('admin/analytics/consultations', AdminAnalyticsConsultationsView.as_view(), name='admin-analytics-consultations'),
    path('admin/audit-logs', AdminAuditLogListView.as_view(), name='admin-audit-logs'),
    path('admin/doctors', AdminDoctorApplicationsListView.as_view(), name='admin-doctor-applications'),
    path('admin/doctors/<uuid:id>/approve', AdminDoctorApproveView.as_view(), name='admin-doctor-approve'),
    path('admin/doctors/<uuid:id>/reject', AdminDoctorRejectView.as_view(), name='admin-doctor-reject'),
    path('admin/doctors/<uuid:id>/remove', AdminDoctorRemoveView.as_view(), name='admin-doctor-remove'),
]


urlpatterns = [
    path('admin/', admin.site.urls),

    # Health Probes
    path('health/live', HealthLiveView.as_view(), name='health-live'),
    path('health/ready', HealthReadyView.as_view(), name='health-ready'),

    # Metrics
    path('metrics', RestrictedMetricsView.as_view(), name='prometheus-metrics'),

    # OpenAPI Schema & Swagger UI Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # API v1 routes
    path('api/v1/', include(api_v1_patterns)),
]
