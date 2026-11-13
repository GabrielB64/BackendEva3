
from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='web/login.html'
        ),
        name='login'
    ),
    path('logout/', views.cerrar_sesion, name='logout'),

    path('', views.dashboard, name='dashboard'),

    path('pedidos/', views.lista_pedidos, name='lista_pedidos'),
    path('pedidos/nuevo/', views.crear_pedido, name='crear_pedido'),
    path(
        'pedidos/<int:pedido_id>/confirmar/',
        views.confirmar_pedido_web,
        name='confirmar_pedido'
    ),

    path('produccion/', views.kanban, name='kanban'),
    path(
        'produccion/<int:orden_id>/avanzar/',
        views.avanzar_orden_web,
        name='avanzar_orden'
    ),

    path('despachos/', views.lista_despachos, name='lista_despachos'),
    path('despachos/nuevo/', views.crear_despacho, name='crear_despacho'),
    path(
        'despachos/<int:despacho_id>/iniciar/',
        views.iniciar_despacho_web,
        name='iniciar_despacho'
    ),
    path(
        'despachos/<int:despacho_id>/entrega/',
        views.confirmar_entrega_web,
        name='confirmar_entrega'
    ),
    path(
        'administracion/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),
    path(
        'administracion/clientes/nuevo/',
        views.crear_cliente,
        name='crear_cliente'
    ),
    path(
        'produccion/<int:orden_id>/entregar/',
        views.entregar_pedido_kanban,
        name='entregar_pedido_kanban'
    ),
    
    
]
