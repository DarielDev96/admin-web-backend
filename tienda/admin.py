from django.contrib import admin
from .models import Turno, Venta, DetalleVenta

admin.site.register(Turno)
admin.site.register(Venta)
admin.site.register(DetalleVenta)
