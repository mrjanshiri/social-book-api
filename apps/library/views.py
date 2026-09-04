from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Shelf
from .serializers import ShelfSerializer


class ShelfViewSet(viewsets.ModelViewSet):
    queryset = Shelf.objects.all()
    serializer_class = ShelfSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Shelf.objects.all()
        if not user.is_staff:
            queryset = Shelf.objects.filter(user=user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)