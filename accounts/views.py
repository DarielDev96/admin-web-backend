
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import RegistroSerializer, LoginSerializer, UsuarioSerializer
from django.contrib.auth import get_user_model
from django.db.models import Q

Usuario = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def registro_view(request):
    # Verificar si es el primer usuario
    is_first_user = not Usuario.objects.exists()

    serializer = RegistroSerializer(data=request.data)
    if serializer.is_valid():
        usuario = serializer.save()

        # Si es el primer usuario, hacerlo superusuario y staff
        if is_first_user:
            usuario.is_superuser = True
            usuario.is_staff = True
            usuario.save(update_fields=['is_superuser', 'is_staff'])

        return Response({
            'message': 'Usuario creado exitosamente',
            'user': UsuarioSerializer(usuario).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UsuarioSerializer(user).data
            })
        return Response({'error': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    serializer = UsuarioSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_usuarios_view(request):
    if request.user.is_superuser or request.user.pymes_propias.exists():
        # Propietarios y superusuarios ven todos los usuarios
        usuarios = Usuario.objects.all()
    else:
        # Empleados/admins ven solo usuarios de sus PYMEs
        from tienda.models import PYME
        pymes = PYME.objects.filter(
            Q(propietario=request.user) |
            Q(administrador=request.user) |
            Q(empleados=request.user)
        )
        usuarios = Usuario.objects.filter(
            Q(pymes_propias__in=pymes) |
            Q(pymes_administradas__in=pymes) |
            Q(pymes_empleado__in=pymes)
        ).distinct()

    serializer = UsuarioSerializer(usuarios, many=True)
    return Response(serializer.data)
