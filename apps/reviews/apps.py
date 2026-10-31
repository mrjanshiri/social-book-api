from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    name = 'apps.reviews'

    def ready(self):
        import apps.reviews.signals