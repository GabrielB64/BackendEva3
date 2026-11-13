
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.db import transaction
from django.shortcuts import get_object_or_404

from pedidos.models import Pedido, Cliente, Producto
from pedidos.services import confirmar_pedido
from produccion.models import OrdenProduccion
from produccion.services import avanzar_etapa
from despachos.models import Despacho
from despachos.services import iniciar_despacho, confirmar_entrega

from .decorators import roles_permitidos
from .forms import (
    PedidoForm,
    DetallePedidoFormSet,
    DespachoForm,
    ComprobanteEntregaForm,
    ClienteForm,
)
from django.db.models import F

from pedidos.models import Pedido
from inventario.models import Insumo
from produccion.models import OrdenProduccion
from despachos.models import Despacho
from .decorators import roles_permitidos


@login_required
def dashboard(request):
    context = {
        'total_pedidos': Pedido.objects.count(),
        'pedidos_pendientes': Pedido.objects.filter(
            estado=Pedido.Estado.COTIZACION
        ).count(),
        'ordenes_produccion': OrdenProduccion.objects.exclude(
            estado=OrdenProduccion.Estado.LISTO
        ).count(),
        'despachos_pendientes': Despacho.objects.exclude(
            estado=Despacho.Estado.ENTREGADO
        ).count(),
        'ultimos_pedidos': Pedido.objects.select_related(
            'cliente'
        ).order_by('-fecha_creacion')[:8],
    }
    return render(request, 'web/dashboard.html', context)


@login_required
@require_POST
def cerrar_sesion(request):
    logout(request)
    return redirect('login')


@roles_permitidos('VENDEDOR')
def lista_pedidos(request):
    pedidos = Pedido.objects.select_related(
        'cliente', 'creado_por'
    ).order_by('-fecha_creacion')

    return render(
        request,
        'web/pedidos_lista.html',
        {'pedidos': pedidos},
    )


@roles_permitidos('VENDEDOR')
def crear_pedido(request):
    if request.method == 'POST':
        form = PedidoForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                pedido = form.save(commit=False)
                pedido.creado_por = request.user
                pedido.save()

                formset = DetallePedidoFormSet(
                    request.POST,
                    instance=pedido
                )

                if formset.is_valid():
                    detalles = formset.save(commit=False)


                    for detalle in detalles:
                        if detalle.cantidad < 1:
                            raise ValueError(
                                'La cantidad debe ser mayor que cero.'
                            )

                        detalle.precio_unitario = (
                            detalle.producto.precio_base
                        )
                        detalle.save()

                    for eliminado in formset.deleted_objects:
                        eliminado.delete()

                    messages.success(
                        request,
                        f'Pedido #{pedido.pk} creado como cotización.'
                    )
                    return redirect('lista_pedidos')

                pedido.delete()
        else:
            formset = DetallePedidoFormSet(request.POST)

    else:
        form = PedidoForm()
        formset = DetallePedidoFormSet()

    return render(
        request,
        'web/pedido_form.html',
        {'form': form, 'formset': formset},
    )


@roles_permitidos('VENDEDOR')
@require_POST
def confirmar_pedido_web(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)

    try:
        confirmar_pedido(pedido.pk, request.user)
        messages.success(
            request,
            f'Pedido #{pedido.pk} confirmado y enviado a producción.'
        )
    except Exception as error:
        messages.error(request, str(error))

    return redirect('lista_pedidos')


@roles_permitidos('COCINA')
def kanban(request):
    estados = OrdenProduccion.Estado.choices

    ordenes_por_estado = []

    for codigo, nombre in estados:
        ordenes = (
            OrdenProduccion.objects
            .filter(estado=codigo)
            .exclude(pedido__estado=Pedido.Estado.ENTREGADO)
            .select_related('pedido', 'pedido__cliente')
            .prefetch_related('pedido__detalles__producto')
            .order_by('pedido__fecha_entrega')
        )

        ordenes_por_estado.append({
            'codigo': codigo,
            'nombre': nombre,
            'ordenes': ordenes,
        })

    return render(
        request,
        'web/kanban.html',
        {'columnas': ordenes_por_estado},
    )



@roles_permitidos('COCINA')
@require_POST
def entregar_pedido_kanban(request, orden_id):
    try:
        with transaction.atomic():
            orden = get_object_or_404(
                OrdenProduccion.objects.select_for_update().select_related('pedido'),
                pk=orden_id
            )

            pedido = orden.pedido

            if orden.estado != OrdenProduccion.Estado.LISTO:
                raise ValueError(
                    'Solo se pueden entregar pedidos cuya producción esté lista.'
                )

            if pedido.estado == Pedido.Estado.ENTREGADO:
                raise ValueError('Este pedido ya fue entregado.')

            if pedido.estado != Pedido.Estado.CONFIRMADO:
                raise ValueError('El pedido no está confirmado.')

            pedido.estado = Pedido.Estado.ENTREGADO
            pedido.save(update_fields=['estado'])

        messages.success(
            request,
            f'Pedido #{pedido.id} marcado como entregado.'
        )

    except Exception as error:
        messages.error(request, str(error))

    return redirect('kanban')



@roles_permitidos('DESPACHO')
def lista_despachos(request):
    despachos = Despacho.objects.select_related(
        'pedido', 'pedido__cliente', 'repartidor'
    ).order_by('fecha_entrega', 'orden_ruta')

    if not request.user.is_superuser and request.user.rol == 'DESPACHO':
        despachos = despachos.filter(repartidor=request.user)

    return render(
        request,
        'web/despachos_lista.html',
        {'despachos': despachos},
    )


@roles_permitidos('DESPACHO')
def crear_despacho(request):
    if request.method == 'POST':
        form = DespachoForm(request.POST)

        if form.is_valid():
            despacho = form.save()
            messages.success(
                request,
                f'Despacho #{despacho.pk} creado correctamente.'
            )
            return redirect('lista_despachos')
    else:
        form = DespachoForm()

    return render(
        request,
        'web/despacho_form.html',
        {'form': form},
    )


@roles_permitidos('DESPACHO')
@require_POST
def iniciar_despacho_web(request, despacho_id):
    despacho = get_object_or_404(Despacho, pk=despacho_id)

    if (
        request.user.rol == 'DESPACHO'
        and despacho.repartidor_id != request.user.pk
    ):
        messages.error(request, 'Este despacho no está asignado a tu usuario.')
        return redirect('lista_despachos')

    try:
        iniciar_despacho(despacho.pk)
        messages.success(request, 'Despacho iniciado.')
    except Exception as error:
        messages.error(request, str(error))

    return redirect('lista_despachos')


@roles_permitidos('DESPACHO')
def confirmar_entrega_web(request, despacho_id):
    despacho = get_object_or_404(Despacho, pk=despacho_id)

    if (
        request.user.rol == 'DESPACHO'
        and despacho.repartidor_id != request.user.pk
    ):
        messages.error(request, 'Este despacho no está asignado a tu usuario.')
        return redirect('lista_despachos')

    if despacho.estado != Despacho.Estado.EN_RUTA:
        messages.error(request, 'El despacho no está en ruta.')
        return redirect('lista_despachos')

    if request.method == 'POST':
        form = ComprobanteEntregaForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():
            try:
                confirmar_entrega(
                    despacho.pk,
                    fotografia=form.cleaned_data['fotografia'],
                    recibido_por=form.cleaned_data['recibido_por'],
                    observaciones=form.cleaned_data['observaciones'],
                )
                messages.success(
                    request,
                    'Entrega confirmada correctamente.'
                )
                return redirect('lista_despachos')
            except Exception as error:
                messages.error(request, str(error))
    else:
        form = ComprobanteEntregaForm()

    return render(
        request,
        'web/entrega_form.html',
        {'form': form, 'despacho': despacho},
    )
@roles_permitidos('ADMINISTRADOR')
def admin_dashboard(request):
    context = {
        'total_pedidos': Pedido.objects.count(),

        'pedidos_cotizacion': Pedido.objects.filter(
            estado='COTIZACION'
        ).count(),

        'pedidos_confirmados': Pedido.objects.filter(
            estado='CONFIRMADO'
        ).count(),

        'ordenes_produccion': OrdenProduccion.objects.exclude(
            estado='LISTO'
        ).count(),

        'despachos_pendientes': Despacho.objects.filter(
            estado__in=['PENDIENTE', 'EN_RUTA']
        ).count(),

        'insumos_bajos': Insumo.objects.filter(
            activo=True,
            stock_actual__lte=F('stock_minimo')
        ).count(),

        'ultimos_pedidos': Pedido.objects.select_related(
            'cliente'
        ).order_by('-fecha_creacion')[:8],

        'insumos_alerta': Insumo.objects.filter(
            activo=True,
            stock_actual__lte=F('stock_minimo')
        ).order_by('nombre')[:8],
    }

    return render(request, 'web/admin_dashboard.html', context)

@roles_permitidos('ADMINISTRADOR')
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente registrado correctamente.')
            return redirect('admin_dashboard')
    else:
        form = ClienteForm()

    return render(request, 'web/cliente_form.html', {
        'form': form
    })
    
def pagina_no_encontrada(request, exception):
    return render(request, '404.html', status=404)

@roles_permitidos('COCINA')
@require_POST
def avanzar_orden_web(request, orden_id):
    try:
        avanzar_etapa(orden_id)
        messages.success(request, 'Orden avanzada correctamente.')
    except Exception as error:
        messages.error(request, str(error))

    return redirect('kanban')