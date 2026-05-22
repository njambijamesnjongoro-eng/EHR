from rest_framework import serializers
from core.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone_number",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "is_active", "created_at"]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
            "phone_number",
        ]

    def validate_role(self, value):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if request.user.role == User.Role.SUPER_ADMIN:
                return value
            if request.user.role == User.Role.HOSPITAL_ADMIN:
                if value in (
                    User.Role.SUPER_ADMIN,
                    User.Role.HOSPITAL_ADMIN,
                ):
                    raise serializers.ValidationError(
                        "Cannot create admin-level users"
                    )
                return value
            raise serializers.ValidationError("Not authorized to create users")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(style={"input_type": "password"})
    new_password = serializers.CharField(style={"input_type": "password"})

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters")
        return value


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()
