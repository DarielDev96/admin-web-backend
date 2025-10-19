# backend/tienda/models.py
from django.db import models
from accounts.models import Usuario


class PYME(models.Model):
    nombre = models.CharField("PYME", max_length=50)
    propietario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='pymes_propias'
    )
    descripcion = models.TextField(blank=True, null=True)
    direccion = models.CharField(max_length=250)
    administrador = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        related_name='pymes_administradas',
        null=True,
        blank=True
    )
    empleados = models.ManyToManyField(
        Usuario,
        blank=True,
        related_name='pymes_empleado'
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'PyME'
        verbose_name_plural = 'PyMEs'

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=50)
    codigo = models.CharField(
        max_length=100, unique=True, blank=True, null=True)
    tienda = models.ForeignKey(
        PYME, on_delete=models.CASCADE, related_name='productos')
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'


class Turno(models.Model):
    pyme = models.ForeignKey(PYME, on_delete=models.CASCADE)
    abierto_por = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='turnos_abiertos'
    )
    cerrado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turnos_cerrados'
    )
    empleados = models.ManyToManyField(
        Usuario,
        related_name='turnos_asignados'
    )
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    # Datos del cierre
    total_ventas = models.DecimalField(
        max_digits=12, decimal_places=2, default=0)
    ganancia_bruta = models.DecimalField(
        max_digits=12, decimal_places=2, default=0)
    salario_empleados = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    salario_admin = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    gastos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notas_gastos = models.TextField(blank=True)

    def __str__(self):
        return f"Turno {self.id} - {self.pyme.nombre}"


class Venta(models.Model):
    METODO_PAGO = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
    ]

    turno = models.ForeignKey(Turno, on_delete=models.CASCADE)
    vendedor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    pyme = models.ForeignKey(PYME, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=15, choices=METODO_PAGO)
    codigo_transferencia = models.CharField(
        max_length=100, blank=True, null=True)
    telefono_cliente = models.CharField(max_length=17, blank=True, null=True)

    def __str__(self):
        return f"Venta {self.id} - {self.total}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(
        Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2)  # Precio de venta
    costo_unitario = models.DecimalField(
        max_digits=10, decimal_places=2)   # Precio de compra

    @property
    def ganancia(self):
        return (self.precio_unitario - self.costo_unitario) * self.cantidad

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
