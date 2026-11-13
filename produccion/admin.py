
from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import OrdenProduccion
from .services import avanzar_etapa


@admin.register(OrdenProduccion)
class OrdenProduccionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'pedido',
        'estado',
        'fecha_inicio',
        'fecha_actualizacion',
    )
    list_filter = ('estado',)
    search_fields = ('pedido__id',)
    readonly_fields = ('fecha_inicio', 'fecha_actualizacion')
    actions = ['avanzar_ordenes']

    @admin.action(description="Avanzar una etapa en el Kanban")
    def avanzar_ordenes(self, request, queryset):
        avanzadas = 0

        for orden in queryset:
            try:
                avanzar_etapa(orden.pk)
                avanzadas += 1
            except ValidationError as error:
                self.message_user(
                    request,
                    f"Orden #{orden.pk}: {' '.join(error.messages)}",
                    level=messages.ERROR,
                )

        if avanzadas:
            self.message_user(
                request,
                f"{avanzadas} orden(es) avanzaron correctamente.",
                level=messages.SUCCESS,
            )
