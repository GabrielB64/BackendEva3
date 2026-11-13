from django.conf import settings
from django.db import models


class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    direccion = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Pedido(models.Model):

    class Estado(models.TextChoices):
        COTIZACION = 'COTIZACION', 'Cotización'
        CONFIRMADO = 'CONFIRMADO', 'Confirmado'
        CANCELADO = 'CANCELADO', 'Cancelado'
        ENTREGADO = 'ENTREGADO', 'Entregado'

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='pedidos'
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='pedidos_creados'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateField()
    hora_entrega = models.TimeField()
    direccion_entrega = models.CharField(max_length=255, blank=True)
    diseno_personalizado = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.COTIZACION
    )
    consumo_inventario_realizado = models.BooleanField(default=False)

    def __str__(self):
        return f"Pedido #{self.pk} - {self.cliente}"

    @property
    def total(self):
        return sum(
            (detalle.subtotal for detalle in self.detalles.all()),
            start=0
        )


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='detalles_pedido'
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    ingredientes_adicionales = models.TextField(blank=True)
    especificaciones = models.TextField(blank=True)

    def __str__(self):
        return f"{self.cantidad} x {self.producto}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario