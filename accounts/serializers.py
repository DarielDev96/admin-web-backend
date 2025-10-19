# backend/accounts/serializers.py
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import Usuario


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Usuario
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        usuario = Usuario.objects.create(
            username=validated_data['username'],
            email=validated_data['email']
        )
        usuario.set_password(validated_data['password'])
        usuario.save()
        return usuario


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ('id', 'username', 'email')
