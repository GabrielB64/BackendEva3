
from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import Despacho, ComprobanteEntrega
from .services import iniciar_despacho


@admin.register(Despacho)
class DespachoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'pedido',
        'repartidor',
        'fecha_entrega',
        'hora_entrega',
        'orden_ruta',
        'estado',
    )
    list_filter = ('estado', 'fecha_entrega')
    search_fields = (
        'pedido__id',
        'repartidor__username',
        'direccion',
    )
    ordering = ('fecha_entrega', 'orden_ruta')
    actions = ['iniciar_despachos']

    @admin.action(description="Iniciar ruta de despachos")
    def iniciar_despachos(self, request, queryset):
        iniciados = 0

        for despacho in queryset:
            try:
                iniciar_despacho(despacho.pk)
                iniciados += 1
            except ValidationError as error:
                self.message_user(
                    request,
                    f"Despacho #{despacho.pk}: {' '.join(error.messages)}",
                    level=messages.ERROR,
                )

        if iniciados:
            self.message_user(
                request,
                f"{iniciados} despacho(s) iniciados correctamente.",
                level=messages.SUCCESS,
            )


@admin.register(ComprobanteEntrega)
class ComprobanteEntregaAdmin(admin.ModelAdmin):
    list_display = (
        'despacho',
        'recibido_por',
        'fecha_confirmacion',
    )
    search_fields = (
        'despacho__pedido__id',
        'recibido_por',
    )
    readonly_fields = (
        'despacho',
        'fotografia',
        'recibido_por',
        'fecha_confirmacion',
        'observaciones',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
