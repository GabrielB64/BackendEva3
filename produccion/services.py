
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import OrdenProduccion


@transaction.atomic
def avanzar_etapa(orden_id):
    orden = (
        OrdenProduccion.objects
        .select_for_update()
        .get(pk=orden_id)
    )

    etapas = [
        OrdenProduccion.Estado.RECIBIDO,
        OrdenProduccion.Estado.EN_PREPARACION,
        OrdenProduccion.Estado.HORNEADO_DECORADO,
        OrdenProduccion.Estado.CONTROL_CALIDAD,
        OrdenProduccion.Estado.LISTO,
    ]

    indice = etapas.index(orden.estado)

    if indice == len(etapas) - 1:
        raise ValidationError(
            "La orden ya se encuentra en la etapa final: Listo."
        )

    orden.estado = etapas[indice + 1]
    orden.save(update_fields=['estado', 'fecha_actualizacion'])

    return orden
