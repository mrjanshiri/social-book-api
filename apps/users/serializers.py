from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "password", "email"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        try:
            return User.objects.create_user(
                username=validated_data["username"],
                password=validated_data["password"],
                email=validated_data["email"]
            )
        except IntegrityError:
            raise serializers.ValidationError("An integrity error occurred. Please try again.")

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already in use.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value


class ProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['username', 'last_name', 'first_name', 'profile_picture', 'email']
        read_only_fields = ['username']

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email cannot be empty.")
        if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff', 'is_superuser']

    def validate(self, attrs):
        requester = self.context['request'].user
        if not requester.is_superuser:
            if 'is_superuser' in attrs:
                raise serializers.ValidationError(
                    {"is_superuser": "Only SuperAdmins can change this."}
                )
            if 'is_staff' in attrs:
                raise serializers.ValidationError(
                    {"is_staff": "Only SuperAdmins can grant or revoke Admin status."}
                )
        return attrs