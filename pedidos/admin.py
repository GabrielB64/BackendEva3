from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from .models import Cliente, Producto, Pedido, DetallePedido
from .services import confirmar_pedido



@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'email')
    search_fields = ('nombre', 'telefono', 'email')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_base', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'cliente', 'fecha_entrega',
        'hora_entrega', 'estado', 'creado_por'
    )
    list_filter = ('estado', 'fecha_entrega')
    search_fields = ('cliente__nombre', 'id')
    inlines = [DetallePedidoInline]
    actions = ['confirmar_pedidos']

    @admin.action(description="Confirmar pedidos seleccionados")
    def confirmar_pedidos(self, request, queryset):
        confirmados = 0
        for pedido in queryset:
            try:
                confirmar_pedido(pedido.pk, request.user)
                confirmados += 1
            except ValidationError as error:
                self.message_user(
                    request,
                    f"Pedido #{pedido.pk}: {' '.join(error.messages)}",
                    level=messages.ERROR
                )

        if confirmados:
            self.message_user(
                request,
                f"{confirmados} pedido(s) confirmado(s) correctamente.",
                level=messages.SUCCESS
            )