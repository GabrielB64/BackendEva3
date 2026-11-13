from django.conf import settings
from django.db import models

from pedidos.models import Pedido


class Despacho(models.Model):

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        EN_RUTA = 'EN_RUTA', 'En Ruta'
        ENTREGADO = 'ENTREGADO', 'Entregado'
        FALLIDO = 'FALLIDO', 'Fallido'

    pedido = models.OneToOneField(
        Pedido,
        on_delete=models.CASCADE,
        related_name='despacho'
    )
    repartidor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='despachos_asignados'
    )
    direccion = models.CharField(max_length=255)
    fecha_entrega = models.DateField()
    hora_entrega = models.TimeField()
    orden_ruta = models.PositiveIntegerField(default=1)
    estado = models.CharField(
        max_length=15,
        choices=Estado.choices,
        default=Estado.PENDIENTE
    )
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Despacho del pedido #{self.pedido_id}"


class ComprobanteEntrega(models.Model):
    despacho = models.OneToOneField(
        Despacho,
        on_delete=models.CASCADE,
        related_name='comprobante'
    )
    fotografia = models.ImageField(upload_to='comprobantes/')
    recibido_por = models.CharField(max_length=150, blank=True)
    fecha_confirmacion = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Comprobante despacho #{self.despacho_id}"