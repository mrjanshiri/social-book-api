from django.db import IntegrityError, transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from .filters import ReviewFilter
from .models import Review
from .permissions import IsReviewOwnerOrAdminDelete
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.select_related('user', 'book')
    serializer_class = ReviewSerializer
    permission_classes = [IsReviewOwnerOrAdminDelete]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ReviewFilter
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError({'book_id': 'You have already reviewed this book.'})