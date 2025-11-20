from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from django.shortcuts import get_object_or_404
from .models import VilaListing
from .serializers import VilaListingSerializer

# Create your views here.


class vila_list(APIView):
    def get(self, request,pk=None):
        if pk:
            vila = VilaListing.objects.get(pk=pk)
            serializer = VilaListingSerializer(vila)
            return Response(serializer.data)
        vila = VilaListing.objects.all()
        serializer = VilaListingSerializer(vila, many=True)
        return Response(serializer.data)

    def post(self,request):
        data = request.data
        serializer = VilaListingSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
