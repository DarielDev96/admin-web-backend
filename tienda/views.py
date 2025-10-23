# backend/tienda/views.py
from datetime import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from accounts.models import Usuario
from .models import PYME, DetalleVenta, Producto, Turno, Venta
from .serializers import PYMECreateSerializer, PYMESerializer, ProductoSerializer, TurnoSerializer, VentaSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_pymes_view(request):
    pymes = PYME.objects.filter(
        Q(propietario=request.user) |
        Q(administrador=request.user) |
        Q(empleados=request.user)
    ).distinct()
    serializer = PYMESerializer(pymes, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_pyme_view(request):
    serializer = PYMECreateSerializer(
        data=request.data, context={'request': request})
    if serializer.is_valid():
        pyme = serializer.save()
        return Response(PYMESerializer(pyme).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_productos_view(request):
    pymes_ids = PYME.objects.filter(
        Q(propietario=request.user) |
        Q(administrador=request.user) |
        Q(empleados=request.user)
    ).values_list('id', flat=True)

    productos = Producto.objects.filter(
        tienda_id__in=pymes_ids)


    serializer = ProductoSerializer(
        productos, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_producto_view(request):
    # Verificar que la tienda pertenezca al usuario
    tienda_id = request.data.get('tienda')
    if not tienda_id:
        return Response({'error': 'Se requiere el ID de la tienda'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        pyme = PYME.objects.get(id=tienda_id)
        if not (pyme.propietario == request.user or pyme.administrador == request.user):
            return Response({'error': 'No tienes permiso para agregar productos a esta tienda'}, status=status.HTTP_403_FORBIDDEN)
    except PYME.DoesNotExist:
        return Response({'error': 'Tienda no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProductoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def abrir_turno_view(request):
    pyme_id = request.data.get('pyme')
    empleados_ids = request.data.get('empleados', [])

    if not pyme_id:
        return Response({'error': 'Se requiere el ID de la PYME'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        pyme = PYME.objects.get(id=pyme_id)
        if not (pyme.propietario == request.user or pyme.administrador == request.user):
            return Response({'error': 'No tienes permiso para abrir turnos en esta PYME'}, status=status.HTTP_403_FORBIDDEN)
    except PYME.DoesNotExist:
        return Response({'error': 'PYME no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    # Verificar que los empleados pertenezcan a la PYME
    empleados_validos = Usuario.objects.filter(
        id__in=empleados_ids,
        pymes_empleado=pyme
    )
    if len(empleados_validos) != len(empleados_ids):
        return Response({'error': 'Algunos empleados no pertenecen a esta PYME'}, status=status.HTTP_400_BAD_REQUEST)

    turno = Turno.objects.create(
        pyme=pyme,
        abierto_por=request.user
    )
    turno.empleados.set(empleados_validos)
    serializer = TurnoSerializer(turno)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registrar_venta_view(request):
    turno_id = request.data.get('turno')
    productos = request.data.get('productos', [])
    metodo_pago = request.data.get('metodo_pago')
    codigo_transferencia = request.data.get('codigo_transferencia', None)
    telefono_cliente = request.data.get('telefono_cliente', None)

    if not turno_id or not productos or not metodo_pago:
        return Response({'error': 'Faltan datos requeridos'}, status=status.HTTP_400_BAD_REQUEST)

    # Validar turno
    try:
        turno = Turno.objects.get(id=turno_id, activo=True)
        if request.user not in turno.empleados.all():
            return Response({'error': 'No estás asignado a este turno'}, status=status.HTTP_403_FORBIDDEN)
    except Turno.DoesNotExist:
        return Response({'error': 'Turno no encontrado o inactivo'}, status=status.HTTP_404_NOT_FOUND)

    # Validar método de pago
    if metodo_pago == 'transferencia':
        if not codigo_transferencia or not telefono_cliente:
            return Response({'error': 'Se requiere código de transferencia y teléfono del cliente'}, status=status.HTTP_400_BAD_REQUEST)

    # Calcular total y crear venta
    total = 0
    venta = Venta.objects.create(
        turno=turno,
        vendedor=request.user,
        pyme=turno.pyme,
        total=0,
        metodo_pago=metodo_pago,
        codigo_transferencia=codigo_transferencia,
        telefono_cliente=telefono_cliente
    )

    # Crear detalles
    for item in productos:
        try:
            producto = Producto.objects.get(
                id=item['producto'], tienda=turno.pyme)
            cantidad = item['cantidad']
            detalle = DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio_venta,
                costo_unitario=producto.precio_compra
            )
            total += producto.precio_venta * cantidad
        except Producto.DoesNotExist:
            venta.delete()
            return Response({'error': f'Producto {item["producto"]} no encontrado en esta tienda'}, status=status.HTTP_400_BAD_REQUEST)

    venta.total = total
    venta.save()

    serializer = VentaSerializer(venta)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cerrar_turno_view(request, turno_id):
    try:
        turno = Turno.objects.get(id=turno_id)
        # Verificar permisos
        if not (turno.pyme.propietario == request.user or turno.pyme.administrador == request.user):
            return Response({'error': 'No tienes permiso para cerrar este turno'}, status=status.HTTP_403_FORBIDDEN)

        if not turno.activo:
            return Response({'error': 'El turno ya está cerrado'}, status=status.HTTP_400_BAD_REQUEST)

        # Calcular totales
        ventas = Venta.objects.filter(turno=turno)
        total_ventas = sum(venta.total for venta in ventas)

        detalles = DetalleVenta.objects.filter(venta__in=ventas)
        ganancia_bruta = sum(detalle.ganancia for detalle in detalles)

        # Actualizar turno con datos del cierre
        turno.total_ventas = total_ventas
        turno.ganancia_bruta = ganancia_bruta
        turno.salario_empleados = request.data.get('salario_empleados', 0)
        turno.salario_admin = request.data.get('salario_admin', 0)
        turno.gastos = request.data.get('gastos', 0)
        turno.notas_gastos = request.data.get('notas_gastos', '')
        turno.cerrado_por = request.user
        turno.fin = timezone.now()
        turno.activo = False
        turno.save()

        serializer = TurnoSerializer(turno)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Turno.DoesNotExist:
        return Response({'error': 'Turno no encontrado'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_turnos_view(request):
    """
    Lista todos los turnos en los que el usuario tiene algún rol:
    - Como propietario o administrador de la PYME (puede ver todos los turnos de esa PYME)
    - Como empleado asignado (solo ve sus propios turnos)
    """
    # Turnos donde el usuario es empleado
    turnos_como_empleado = Turno.objects.filter(empleados=request.user)

    # Turnos de PYMEs donde es propietario o administrador
    pymes_gestionadas = PYME.objects.filter(
        Q(propietario=request.user) | Q(administrador=request.user)
    )
    turnos_como_gestor = Turno.objects.filter(pyme__in=pymes_gestionadas)

    # Combinar y ordenar
    turnos = (turnos_como_empleado |
              turnos_como_gestor).distinct().order_by('-inicio')

    serializer = TurnoSerializer(turnos, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detalle_pyme_view(request, pyme_id):
    try:
        pyme = PYME.objects.get(id=pyme_id)
        # Verificar acceso
        if not (
            pyme.propietario == request.user or
            pyme.administrador == request.user or
            pyme.empleados.filter(id=request.user.id).exists()
        ):
            return Response({'error': 'No tienes acceso a esta PYME'}, status=403)
        serializer = PYMESerializer(pyme)
        return Response(serializer.data)
    except PYME.DoesNotExist:
        return Response({'error': 'PYME no encontrada'}, status=404)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def actualizar_pyme_view(request, pyme_id):
    try:
        pyme = PYME.objects.get(id=pyme_id)
        if pyme.propietario != request.user:
            return Response({'error': 'Solo el propietario puede editar la PYME'}, status=403)

        serializer = PYMECreateSerializer(
            pyme, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(PYMESerializer(pyme).data)
        return Response(serializer.errors, status=400)
    except PYME.DoesNotExist:
        return Response({'error': 'PYME no encontrada'}, status=404)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def actualizar_producto_view(request, producto_id):
    try:
        producto = Producto.objects.get(id=producto_id)
        pyme = producto.tienda

        # Verificar permisos
        if not (pyme.propietario == request.user or pyme.administrador == request.user):
            return Response({'error': 'Solo el propietario o administrador puede editar productos'}, status=403)

        serializer = ProductoSerializer(
            producto, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    except Producto.DoesNotExist:
        return Response({'error': 'Producto no encontrado'}, status=404)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_producto_view(request, producto_id):
    try:
        producto = Producto.objects.get(id=producto_id)
        pyme = producto.tienda

        if not (pyme.propietario == request.user or pyme.administrador == request.user):
            return Response({'error': 'Solo el propietario o administrador puede eliminar productos'}, status=403)

        producto.delete()
        return Response(status=204)
    except Producto.DoesNotExist:
        return Response({'error': 'Producto no encontrado'}, status=404)
