from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Alert
from .services import alert_payload, refresh_alerts_for_user


class AlertList(APIView):
    def get(self, request):
        alerts = Alert.objects.filter(owner_user=request.user, dismissed_at__isnull=True).order_by("-created_at")
        return Response([alert_payload(item) for item in alerts])


class AlertRefresh(APIView):
    def post(self, request):
        refresh_alerts_for_user(request.user)
        alerts = Alert.objects.filter(owner_user=request.user, dismissed_at__isnull=True).order_by("-created_at")
        return Response([alert_payload(item) for item in alerts])


class AlertRead(APIView):
    def patch(self, request, alert_id):
        try:
            alert = Alert.objects.get(owner_user=request.user, id=alert_id)
        except Alert.DoesNotExist:
            return Response({"error": "Alert not found"}, status=status.HTTP_404_NOT_FOUND)
        alert.read_at = timezone.now()
        alert.save(update_fields=["read_at", "updated_at"])
        return Response(alert_payload(alert))


class AlertDismiss(APIView):
    def patch(self, request, alert_id):
        try:
            alert = Alert.objects.get(owner_user=request.user, id=alert_id)
        except Alert.DoesNotExist:
            return Response({"error": "Alert not found"}, status=status.HTTP_404_NOT_FOUND)
        alert.dismissed_at = timezone.now()
        alert.save(update_fields=["dismissed_at", "updated_at"])
        return Response(alert_payload(alert))
