
from django import forms
from django.forms import inlineformset_factory
from pedidos.models import Cliente, Pedido, DetallePedido

from pedidos.models import Pedido, DetallePedido
from despachos.models import Despacho, ComprobanteEntrega
from usuarios.models import Usuario


class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = [
            'cliente',
            'fecha_entrega',
            'hora_entrega',
            'direccion_entrega',
            'diseno_personalizado',
            'observaciones',
        ]
        widgets = {
            'fecha_entrega': forms.DateInput(attrs={'type': 'date'}),
            'hora_entrega': forms.TimeInput(attrs={'type': 'time'}),
            'diseno_personalizado': forms.Textarea(attrs={'rows': 2}),
            'observaciones': forms.Textarea(attrs={'rows': 2}),
        }

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'telefono', 'email', 'direccion']


DetallePedidoFormSet = inlineformset_factory(
    Pedido,
    DetallePedido,
    fields=[
        'producto',
        'cantidad',
        'ingredientes_adicionales',
        'especificaciones',
    ],
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True,
    widgets={
        'cantidad': forms.NumberInput(attrs={'min': 1}),
        'ingredientes_adicionales': forms.Textarea(attrs={'rows': 2}),
        'especificaciones': forms.Textarea(attrs={'rows': 2}),
    },
)


class DespachoForm(forms.ModelForm):
    class Meta:
        model = Despacho
        fields = [
            'pedido',
            'repartidor',
            'direccion',
            'fecha_entrega',
            'hora_entrega',
            'orden_ruta',
        ]
        widgets = {
            'fecha_entrega': forms.DateInput(attrs={'type': 'date'}),
            'hora_entrega': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from pedidos.models import Pedido

        self.fields['pedido'].queryset = Pedido.objects.filter(
            estado=Pedido.Estado.CONFIRMADO
        ).exclude(despacho__isnull=False)

        self.fields['repartidor'].queryset = Usuario.objects.filter(
            rol=Usuario.Rol.DESPACHO,
            is_active=True,
        )


class ComprobanteEntregaForm(forms.ModelForm):
    class Meta:
        model = ComprobanteEntrega
        fields = [
            'fotografia',
            'recibido_por',
            'observaciones',
        ]
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 2}),
        }
