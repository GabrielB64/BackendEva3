
from django.core.exceptions import ValidationError
from django.db import transaction

from pedidos.models import Pedido
from produccion.models import OrdenProduccion

from .models import Despacho, ComprobanteEntrega


@transaction.atomic
def iniciar_despacho(despacho_id):
    despacho = (
        Despacho.objects
        .select_for_update()
        .select_related('pedido')
        .get(pk=despacho_id)
    )

    if despacho.estado != Despacho.Estado.PENDIENTE:
        raise ValidationError(
            "Solo se pueden iniciar despachos pendientes."
        )

    try:
        orden = OrdenProduccion.objects.get(pedido=despacho.pedido)
    except OrdenProduccion.DoesNotExist:
        raise ValidationError(
            "El pedido no tiene una orden de producción."
        )

    if orden.estado != OrdenProduccion.Estado.LISTO:
        raise ValidationError(
            "El pedido debe estar listo en producción antes del despacho."
        )

    despacho.estado = Despacho.Estado.EN_RUTA
    despacho.save(update_fields=['estado'])

    return despacho


@transaction.atomic
def confirmar_entrega(
    despacho_id,
    fotografia,
    recibido_por='',
    observaciones=''
):
    despacho = (
        Despacho.objects
        .select_for_update()
        .select_related('pedido')
        .get(pk=despacho_id)
    )

    if despacho.estado != Despacho.Estado.EN_RUTA:
        raise ValidationError(
            "Solo se pueden confirmar entregas de despachos en ruta."
        )

    if not fotografia:
        raise ValidationError(
            "Debes adjuntar una fotografía como comprobante."
        )

    if ComprobanteEntrega.objects.filter(despacho=despacho).exists():
        raise ValidationError(
            "Este despacho ya tiene un comprobante de entrega."
        )

    comprobante = ComprobanteEntrega.objects.create(
        despacho=despacho,
        fotografia=fotografia,
        recibido_por=recibido_por,
        observaciones=observaciones,
    )

    despacho.estado = Despacho.Estado.ENTREGADO
    despacho.save(update_fields=['estado'])

    despacho.pedido.estado = Pedido.Estado.ENTREGADO
    despacho.pedido.save(update_fields=['estado'])

    return comprobante
