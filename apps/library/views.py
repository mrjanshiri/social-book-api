from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import WishlistItem
from .serializers import WhisListItemSerializer


class WhishListItemViewSet(viewsets.ModelViewSet):
    queryset = WishlistItem.objects.all()
    serializer_class = WhisListItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = WishlistItem.objects.all()
        if not user.is_staff:
            queryset = WishlistItem.objects.filter(user=user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)