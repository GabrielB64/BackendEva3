from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Pedido
from inventario.models import (
    Insumo,
    RecetaBOM,
    DetalleBOM,
    MovimientoInventario,
)
from produccion.models import OrdenProduccion


@transaction.atomic
def confirmar_pedido(pedido_id, usuario):
    pedido = (
        Pedido.objects
        .select_for_update()
        .get(pk=pedido_id)
    )

    if pedido.estado != Pedido.Estado.COTIZACION:
        raise ValidationError(
            "Solo se pueden confirmar pedidos en estado de cotización."
        )

    if pedido.consumo_inventario_realizado:
        raise ValidationError(
            "El inventario de este pedido ya fue descontado."
        )

    detalles = list(
        pedido.detalles.select_related('producto')
    )

    if not detalles:
        raise ValidationError(
            "No se puede confirmar un pedido sin productos."
        )

    requerimientos = defaultdict(lambda: Decimal('0'))

    for detalle in detalles:
        receta = RecetaBOM.objects.filter(
            producto=detalle.producto
        ).first()

        if receta is None:
            raise ValidationError(
                f"El producto {detalle.producto.nombre} no tiene una receta BOM."
            )

        componentes = DetalleBOM.objects.filter(
            receta=receta
        )

        if not componentes.exists():
            raise ValidationError(
                f"La receta de {detalle.producto.nombre} no contiene insumos."
            )

        for componente in componentes:
            requerimientos[componente.insumo_id] += (
                componente.cantidad * detalle.cantidad
            )

    # Bloqueamos los insumos para evitar modificaciones simultáneas.
    insumos = {
        insumo.pk: insumo
        for insumo in Insumo.objects.select_for_update()
        .filter(pk__in=sorted(requerimientos.keys()))
        .order_by('pk')
    }

    # Comprobar que existe stock suficiente antes de descontar.
    for insumo_id, cantidad in requerimientos.items():
        insumo = insumos[insumo_id]

        if insumo.stock_actual < cantidad:
            raise ValidationError(
                f"Stock insuficiente de {insumo.nombre}. "
                f"Disponible: {insumo.stock_actual} {insumo.unidad}. "
                f"Necesario: {cantidad} {insumo.unidad}."
            )

    # Descontar insumos y registrar movimientos.
    for insumo_id, cantidad in requerimientos.items():
        insumo = insumos[insumo_id]
        insumo.stock_actual -= cantidad
        insumo.save(update_fields=['stock_actual'])

        MovimientoInventario.objects.create(
            insumo=insumo,
            tipo=MovimientoInventario.Tipo.SALIDA,
            cantidad=cantidad,
            pedido=pedido,
            usuario=usuario,
            observacion=f"Consumo automático del pedido #{pedido.pk}"
        )

    pedido.estado = Pedido.Estado.CONFIRMADO
    pedido.consumo_inventario_realizado = True
    pedido.save(update_fields=[
        'estado',
        'consumo_inventario_realizado'
    ])

    OrdenProduccion.objects.create(pedido=pedido)

    return pedido