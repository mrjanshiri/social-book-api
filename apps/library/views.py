from rest_framework import viewsets
from .models import Shelf
from .serializers import ShelfSerializer
from .permissions import IsShelfOwnerOrReadOnly


class ShelfViewSet(viewsets.ModelViewSet):
    serializer_class = ShelfSerializer
    permission_classes = [IsShelfOwnerOrReadOnly]

    def get_queryset(self):
        request_user = self.request.user
        user_param = self.request.query_params.get('user')
        status_param = self.request.query_params.get('status')

        if user_param:
            queryset = Shelf.objects.filter(user_id=user_param)

            if str(request_user.id) != str(user_param):
                queryset = queryset.filter(is_private=False)
        else:
            queryset = Shelf.objects.filter(user=request_user)

        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset.select_related(
            'user', 'book', 'book__author', 'book__publisher'
        ).prefetch_related('book__categories')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)