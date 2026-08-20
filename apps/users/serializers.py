from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import IntegrityError 
from apps.users.models import Account
User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "password", "email"]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        print(validated_data)
        try:
            user = User.objects.create_user(
                username=validated_data["username"],
                password=validated_data["password"],
                email=validated_data["email"]
            )
            return user
        
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
        fields = ['id', 'last_name', 'first_name', 'profile_picture', 'email']
        read_only_fields = ['id', 'username']

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email cannot be empty.")
        if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value
    


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'username', 'email', 'role']

    def update(self, instance, validated_data):
        # Prevent assigning SuperAdmin role by non-SuperAdmin
        if validated_data.get('role') == 'superadmin' and self.context['request'].user.role != 'superadmin':
            raise serializers.ValidationError("Only SuperAdmins can assign the SuperAdmin role.")

        # If an admin tries to remove their own superadmin status
        if instance.role == 'superadmin' and validated_data.get('role') == 'user':
            superadmin_count = Account.objects.filter(role='superadmin').count()
            if superadmin_count <= 1:
                raise serializers.ValidationError("Cannot remove the last SuperAdmin.")

        return super().update(instance, validated_data)
