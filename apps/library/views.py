from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from .models import Shelf
from .serializers import ShelfSerializer
from .permissions import IsShelfOwnerOrReadOnly
from django.db import transaction, IntegrityError

class ShelfViewSet(viewsets.ModelViewSet):
    serializer_class = ShelfSerializer
    permission_classes = [IsShelfOwnerOrReadOnly]
    lookup_field = 'book_id'

    def get_queryset(self):
        # NOTE Intentional: viewing another user's shelf (list or detail)
        # always requires an explicit ?user=<id>. No implicit fallback.
        request_user = self.request.user
        user_param = self.request.query_params.get('user')
        status_param = self.request.query_params.get('status')
        if user_param:
            try:
                user_param = int(user_param)
            except (TypeError, ValueError):
                raise ValidationError({"user": "Must be a valid integer id."})

            queryset = Shelf.objects.filter(user_id=user_param)
            if not request_user.is_authenticated or request_user.id != user_param:
                queryset = queryset.filter(is_private=False)
        elif request_user.is_authenticated:
            queryset = Shelf.objects.filter(user=request_user)
        else:
            raise ValidationError({
                "detail": "Log in to see your own shelf, or add ?user=<id> to view someone else's public shelf."
            })

        if status_param:
            valid_statuses = [choice[0] for choice in Shelf.STATUS_CHOICES]
            if status_param not in valid_statuses:
                raise ValidationError({"status": f"Must be one of: {', '.join(valid_statuses)}."})
            queryset = queryset.filter(status=status_param)

        return queryset.select_related(
            'user', 'book', 'book__author', 'book__publisher'
        ).prefetch_related('book__categories')

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError({"book_id": "This book is already on your shelf."})