from django.conf import settings
from django.db import models

from pedidos.models import Producto, Pedido


class Insumo(models.Model):

    class Unidad(models.TextChoices):
        GRAMOS = 'g', 'Gramos'
        KILOGRAMOS = 'kg', 'Kilogramos'
        MILILITROS = 'ml', 'Mililitros'
        LITROS = 'l', 'Litros'
        UNIDADES = 'un', 'Unidades'

    nombre = models.CharField(max_length=150)
    unidad = models.CharField(max_length=5, choices=Unidad.choices)
    stock_actual = models.DecimalField(
        max_digits=12, decimal_places=3, default=0
    )
    stock_minimo = models.DecimalField(
        max_digits=12, decimal_places=3, default=0
    )
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.stock_actual} {self.unidad})"


class RecetaBOM(models.Model):
    producto = models.OneToOneField(
        Producto,
        on_delete=models.CASCADE,
        related_name='receta'
    )
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return f"Receta: {self.producto}"


class DetalleBOM(models.Model):
    receta = models.ForeignKey(
        RecetaBOM,
        on_delete=models.CASCADE,
        related_name='insumos'
    )
    insumo = models.ForeignKey(
        Insumo,
        on_delete=models.PROTECT,
        related_name='recetas'
    )
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['receta', 'insumo'],
                name='insumo_unico_por_receta'
            )
        ]

    def __str__(self):
        return f"{self.insumo}: {self.cantidad} {self.insumo.unidad}"


class MovimientoInventario(models.Model):

    class Tipo(models.TextChoices):
        ENTRADA = 'ENTRADA', 'Entrada'
        SALIDA = 'SALIDA', 'Salida'
        AJUSTE = 'AJUSTE', 'Ajuste'

    insumo = models.ForeignKey(
        Insumo,
        on_delete=models.PROTECT,
        related_name='movimientos'
    )
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    fecha = models.DateTimeField(auto_now_add=True)
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_inventario'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='movimientos_inventario'
    )
    observacion = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.tipo}: {self.insumo} - {self.cantidad}"