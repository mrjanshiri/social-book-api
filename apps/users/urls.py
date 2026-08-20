from django.urls import path , include
from .views import SignupView , UserProfileView , UserViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users' , UserViewSet , basename='user')
urlpatterns = [
    path("signup/", SignupView.as_view()),
    path("login/", TokenObtainPairView.as_view()),       # login
    path("refresh/", TokenRefreshView.as_view()),  
    path("user_profile/" , UserProfileView.as_view()),
    path('', include(router.urls)),
]



