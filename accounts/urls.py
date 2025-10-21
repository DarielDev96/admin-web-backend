# backend/accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.registro_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('me/', views.me_view, name='me'),
    path('usuarios/', views.listar_usuarios_view, name='listar_usuarios'),
]
