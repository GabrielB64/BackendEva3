from django.db import models

from pedidos.models import Pedido


class OrdenProduccion(models.Model):

    class Estado(models.TextChoices):
        RECIBIDO = 'RECIBIDO', 'Recibido'
        EN_PREPARACION = 'EN_PREPARACION', 'En Preparación'
        HORNEADO_DECORADO = 'HORNEADO_DECORADO', 'Horneado/Decorado'
        CONTROL_CALIDAD = 'CONTROL_CALIDAD', 'Control de Calidad'
        LISTO = 'LISTO', 'Listo'

    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name='orden_produccion'
    )
    estado = models.CharField(
        max_length=25,
        choices=Estado.choices,
        default=Estado.RECIBIDO
    )
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Producción del pedido #{self.pedido_id}"