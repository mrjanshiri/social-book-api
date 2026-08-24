from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db import transaction
from .serializers import SignupSerializer, ProfileSerializer, UserSerializer
from rest_framework.permissions import IsAuthenticated
from .models import Account
from .utils import would_remove_last_superuser
from apps.core.permissions import IsSuperAdminOrAdmin
from rest_framework import viewsets

User = get_user_model()


class SignupView(APIView):
    serializer_class = SignupSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "user created", "user_id": user.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        data = request.data.copy()
        if 'profile_picture' in request.FILES:
            data['profile_picture'] = request.FILES['profile_picture']
        elif 'profile_picture' in data and data['profile_picture'] is None:
            data['profile_picture'] = None

        serializer = self.serializer_class(request.user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsSuperAdminOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Account.objects.all()
        return Account.objects.filter(pk=user.pk)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            user_to_update = self.get_object()
            new_value = request.data.get('is_superuser', user_to_update.is_superuser)
            if would_remove_last_superuser(user_to_update, new_value):
                return Response({"detail": "Cannot demote the last SuperAdmin."}, status=403)
            return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            user_to_delete = self.get_object()
            if would_remove_last_superuser(user_to_delete, False):
                return Response({"detail": "Cannot delete the last SuperAdmin."}, status=403)
            return super().destroy(request, *args, **kwargs)