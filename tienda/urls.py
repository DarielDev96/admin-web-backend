# backend/tienda/urls.py
from django.urls import path
from . import views

urlpatterns = [

    # pymes
    path('pymes/', views.listar_pymes_view, name='listar_pymes'),
    path('pymes/crear/', views.crear_pyme_view, name='crear_pyme'),
    path('pymes/<int:pyme_id>/', views.detalle_pyme_view, name='detalle_pyme'),

    # Productos
    path('productos/', views.listar_productos_view, name='listar_productos'),
    path('productos/crear/', views.crear_producto_view, name='crear_producto'),

    # Turnos
    path('turnos/abrir/', views.abrir_turno_view, name='abrir_turno'),
    path('ventas/registrar/', views.registrar_venta_view, name='registrar_venta'),
    path('turnos/<int:turno_id>/cerrar/',
         views.cerrar_turno_view, name='cerrar_turno'),
    path('turnos/', views.listar_turnos_view, name='listar_turnos'),
]
