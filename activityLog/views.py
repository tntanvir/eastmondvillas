from django.shortcuts import render
from auditlog.models import LogEntry
from rest_framework.generics import ListAPIView

from rest_framework.response import Response
from rest_framework import status
from .serializers import LogEntrySerializer
# Create your views here.
class ActivityLogView(ListAPIView):
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer


    def get(self, request, *args, **kwargs):
        try:
            logs = self.get_queryset()
            serializer = self.get_serializer(logs, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
