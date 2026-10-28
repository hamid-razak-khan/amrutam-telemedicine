from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.accounts.models import User
from apps.doctors.models import DoctorProfile
from apps.consultations.models import Consultation
from apps.payments.models import Payment
from apps.common.permissions import IsAdminUserRole

class AdminAnalyticsOverviewView(APIView):
    """
    Administrator overview metrics: user counts, active doctors, consultation counts by status,
    revenue totals, and cancellation rates.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    @extend_schema(summary="Platform operational and clinical metrics overview")
    def get(self, request):
        total_patients = User.objects.filter(role=User.ROLE_PATIENT).count()
        total_doctors = User.objects.filter(role=User.ROLE_DOCTOR).count()
        active_verified_doctors = DoctorProfile.objects.filter(
            active_status=True,
            verification_status=DoctorProfile.STATUS_VERIFIED
        ).count()

        total_consultations = Consultation.objects.count()

        # Aggregation of consultations by status
        status_counts = Consultation.objects.values('status').annotate(count=Count('id'))
        status_dict = {item['status']: item['count'] for item in status_counts}

        cancelled_count = status_dict.get(Consultation.STATUS_CANCELLED, 0)
        cancellation_rate = round((cancelled_count / total_consultations * 100), 2) if total_consultations > 0 else 0.0

        # Payments aggregation
        payment_stats = Payment.objects.aggregate(
            total_revenue=Sum('amount', filter=Q(status=Payment.STATUS_COMPLETED)),
            completed_count=Count('id', filter=Q(status=Payment.STATUS_COMPLETED)),
            failed_count=Count('id', filter=Q(status=Payment.STATUS_FAILED))
        )

        return Response({
            "success": True,
            "metrics": {
                "users": {
                    "total_patients": total_patients,
                    "total_doctors": total_doctors,
                    "active_verified_doctors": active_verified_doctors,
                },
                "consultations": {
                    "total_count": total_consultations,
                    "by_status": status_dict,
                    "cancellation_rate_percentage": cancellation_rate,
                },
                "financials": {
                    "gross_revenue": float(payment_stats['total_revenue'] or 0.0),
                    "currency": "INR",
                    "successful_transactions": payment_stats['completed_count'],
                    "failed_transactions": payment_stats['failed_count'],
                }
            }
        }, status=status.HTTP_200_OK)

class AdminAnalyticsConsultationsView(APIView):
    """
    Time-series consultation trends for Recharts dashboard visualizations.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    @extend_schema(
        summary="Daily consultation trend analytics",
        parameters=[
            OpenApiParameter('days', int, description="Number of past days to analyze (default: 14)")
        ]
    )
    def get(self, request):
        from collections import defaultdict

        try:
            days = int(request.query_params.get('days', 14))
        except (ValueError, TypeError):
            days = 14

        days = max(1, min(days, 90))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days - 1)

        # Single query spanning the entire date range
        consultations = Consultation.objects.filter(
            scheduled_start__date__gte=start_date,
            scheduled_start__date__lte=end_date
        ).values('scheduled_start__date', 'status')

        day_stats = defaultdict(lambda: {'total': 0, 'completed': 0, 'cancelled': 0, 'booked': 0})
        for c in consultations:
            d_val = c.get('scheduled_start__date')
            if d_val:
                d_str = d_val.strftime("%Y-%m-%d")
                day_stats[d_str]['total'] += 1
                st = c.get('status')
                if st == Consultation.STATUS_COMPLETED:
                    day_stats[d_str]['completed'] += 1
                elif st == Consultation.STATUS_CANCELLED:
                    day_stats[d_str]['cancelled'] += 1
                elif st in (Consultation.STATUS_BOOKED, Consultation.STATUS_CONFIRMED):
                    day_stats[d_str]['booked'] += 1

        daily_data = []
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            d_str = current_date.strftime("%Y-%m-%d")
            stats = day_stats[d_str]
            daily_data.append({
                "date": d_str,
                "display_date": current_date.strftime("%b %d"),
                "total": stats['total'],
                "completed": stats['completed'],
                "cancelled": stats['cancelled'],
                "booked": stats['booked']
            })

        return Response({"success": True, "trends": daily_data}, status=status.HTTP_200_OK)

