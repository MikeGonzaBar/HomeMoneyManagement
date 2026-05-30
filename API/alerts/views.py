from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Alert
from .services import alert_payload, refresh_alerts_for_user


class AlertList(APIView):
    """List active alerts for the authenticated user."""

    @extend_schema(tags=["Alerts"], responses={200: OpenApiResponse(description="Active alerts")})
    def get(self, request: Request) -> Response:
        """Return non-dismissed alerts ordered newest first."""
        alerts = Alert.objects.filter(owner_user=request.user, dismissed_at__isnull=True).order_by("-created_at")
        return Response([alert_payload(item) for item in alerts])


class AlertRefresh(APIView):
    """Regenerate alerts for the authenticated user."""

    @extend_schema(tags=["Alerts"], request=None, responses={200: OpenApiResponse(description="Refreshed alerts")})
    def post(self, request: Request) -> Response:
        """Refresh alert state and return active alerts."""
        refresh_alerts_for_user(request.user)
        alerts = Alert.objects.filter(owner_user=request.user, dismissed_at__isnull=True).order_by("-created_at")
        return Response([alert_payload(item) for item in alerts])


class AlertRead(APIView):
    """Mark an alert as read."""

    @extend_schema(tags=["Alerts"], request=None, responses={200: OpenApiResponse(description="Alert marked read")})
    def patch(self, request: Request, alert_id: int) -> Response:
        """Set read_at on one alert owned by the authenticated user."""
        try:
            alert = Alert.objects.get(owner_user=request.user, id=alert_id)
        except Alert.DoesNotExist:
            return Response({"error": "Alert not found"}, status=status.HTTP_404_NOT_FOUND)
        alert.read_at = timezone.now()
        alert.save(update_fields=["read_at", "updated_at"])
        return Response(alert_payload(alert))


class AlertDismiss(APIView):
    """Dismiss an alert."""

    @extend_schema(tags=["Alerts"], request=None, responses={200: OpenApiResponse(description="Alert dismissed")})
    def patch(self, request: Request, alert_id: int) -> Response:
        """Set dismissed_at on one alert owned by the authenticated user."""
        try:
            alert = Alert.objects.get(owner_user=request.user, id=alert_id)
        except Alert.DoesNotExist:
            return Response({"error": "Alert not found"}, status=status.HTTP_404_NOT_FOUND)
        alert.dismissed_at = timezone.now()
        alert.save(update_fields=["dismissed_at", "updated_at"])
        return Response(alert_payload(alert))
