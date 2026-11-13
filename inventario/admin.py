from django.contrib import admin
from .models import (
    Insumo, RecetaBOM, DetalleBOM, MovimientoInventario
)


class DetalleBOMInline(admin.TabularInline):
    model = DetalleBOM
    extra = 1


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'unidad', 'stock_actual', 'stock_minimo', 'activo')
    list_filter = ('unidad', 'activo')
    search_fields = ('nombre',)


@admin.register(RecetaBOM)
class RecetaBOMAdmin(admin.ModelAdmin):
    list_display = ('producto',)
    search_fields = ('producto__nombre',)
    inlines = [DetalleBOMInline]


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('insumo', 'tipo', 'cantidad', 'fecha', 'pedido', 'usuario')
    list_filter = ('tipo', 'fecha')
    search_fields = ('insumo__nombre', 'observacion')