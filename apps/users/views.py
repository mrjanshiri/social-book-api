from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import SignupSerializer , ProfileSerializer , UserSerializer
from rest_framework.permissions import IsAuthenticated
from .models import Account
from .permissions import IsSuperAdminOrAdmin
from rest_framework import viewsets

User = get_user_model()

class SignupView(APIView):
    serializer_class = SignupSerializer 

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "user created", "user_id": user.id}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()

        if 'profile_picture' in request.FILES:
            data['profile_picture'] = request.FILES['profile_picture']
        elif 'profile_picture' in data and data['profile_picture'] is None:
            data['profile_picture'] = None


        serializer = self.serializer_class(user, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsSuperAdminOrAdmin]

    def update(self, request, *args, **kwargs):
        user_to_update = self.get_object()

        # Prevent demotion of the last superadmin by an admin
        # This logic is specific and not covered by has_object_permission alone
        if user_to_update.role == 'superadmin' and request.user.role == 'admin':
            superadmin_count = Account.objects.filter(role='superadmin').count()
            if superadmin_count <= 1:
                return Response({"detail": "Cannot modify the last SuperAdmin."}, status=403)

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        user_to_delete = self.get_object()

        # Prevent deletion of the last superadmin
        # This logic is specific and not covered by has_object_permission alone
        if user_to_delete.role == 'superadmin':
            superadmin_count = Account.objects.filter(role='superadmin').count()
            if superadmin_count <= 1:
                return Response({"detail": "Cannot delete the last SuperAdmin."}, status=403)

        return super().destroy(request, *args, **kwargs)