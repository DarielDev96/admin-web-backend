# backend/tienda/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PYME, DetalleVenta, Producto, Turno, Venta

Usuario = get_user_model()


class PYMECreateSerializer(serializers.ModelSerializer):
    administrador = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        required=False,
        allow_null=True
    )
    empleados = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = PYME
        fields = ['nombre', 'descripcion',
                  'direccion', 'administrador', 'empleados']
        extra_kwargs = {
            'descripcion': {'required': False},
            'direccion': {'required': True}
        }

    def create(self, validated_data):
        empleados = validated_data.pop('empleados', [])
        pyme = PYME.objects.create(
            propietario=self.context['request'].user,
            **validated_data
        )
        pyme.empleados.set(empleados)
        return pyme


class PYMESerializer(serializers.ModelSerializer):
    propietario = serializers.StringRelatedField()
    administrador = serializers.StringRelatedField()
    empleados = serializers.StringRelatedField(many=True)

    class Meta:
        model = PYME
        fields = '__all__'


class ProductoSerializer(serializers.ModelSerializer):
    tienda_nombre = serializers.CharField(
        source='tienda.nombre', read_only=True)

    class Meta:
        model = Producto
        fields = '__all__'
        read_only_fields = ['tienda_nombre']


class DetalleVentaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(
        source='producto.nombre', read_only=True)

    class Meta:
        model = DetalleVenta
        fields = ['id', 'producto', 'producto_nombre',
                  'cantidad', 'precio_unitario', 'costo_unitario']


class VentaSerializer(serializers.ModelSerializer):
    detalles = DetalleVentaSerializer(many=True, read_only=True)
    vendedor_nombre = serializers.CharField(
        source='vendedor.username', read_only=True)

    class Meta:
        model = Venta
        fields = '__all__'


class TurnoSerializer(serializers.ModelSerializer):
    empleados_nombres = serializers.StringRelatedField(
        many=True, source='empleados', read_only=True)
    abierto_por_nombre = serializers.CharField(
        source='abierto_por.username', read_only=True)

    class Meta:
        model = Turno
        fields = '__all__'
