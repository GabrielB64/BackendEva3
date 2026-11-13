
from datetime import time, timedelta
from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw

from usuarios.models import Usuario
from pedidos.models import Cliente, Producto, Pedido, DetallePedido
from pedidos.services import confirmar_pedido
from inventario.models import (
    Insumo,
    RecetaBOM,
    DetalleBOM,
    MovimientoInventario,
)
from produccion.models import OrdenProduccion
from produccion.services import avanzar_etapa
from despachos.models import Despacho
from despachos.services import iniciar_despacho, confirmar_entrega


class Command(BaseCommand):
    help = 'Crea datos de demostración para Dulce Arte'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos de demostración...')

        # -------------------------------------------------
        # 1. Usuarios
        # -------------------------------------------------

        usuarios_demo = {}

        for username, rol in [
            ('vendedor_demo', 'VENDEDOR'),
            ('cocina_demo', 'COCINA'),
            ('despacho_demo', 'DESPACHO'),
        ]:
            usuario = Usuario.objects.filter(username=username).first()

            if usuario is None:
                usuario = Usuario.objects.create_user(
                    username=username,
                    password='DulceArteDemo2026!',
                    rol=rol,
                )
            else:
                usuario.rol = rol
                usuario.save(update_fields=['rol'])

            usuarios_demo[rol] = usuario

        vendedor = usuarios_demo['VENDEDOR']
        repartidor = usuarios_demo['DESPACHO']

        # -------------------------------------------------
        # 2. Clientes
        # -------------------------------------------------

        clientes_data = [
            ('Camila Rojas', '912345678', 'camila.demo@example.com',
             'Av. Alemania 123, Temuco'),
            ('Matías González', '923456789', 'matias.demo@example.com',
             'Av. Pablo Neruda 456, Temuco'),
            ('Valentina Muñoz', '934567890', 'valentina.demo@example.com',
             'Centro, Temuco'),
            ('Sebastián Pérez', '945678901', 'sebastian.demo@example.com',
             'Labranza, Temuco'),
            ('Fernanda Soto', '956789012', 'fernanda.demo@example.com',
             'Padre Las Casas, Temuco'),
        ]

        clientes = []

        for nombre, telefono, email, direccion in clientes_data:
            cliente, _ = Cliente.objects.get_or_create(
                email=email,
                defaults={
                    'nombre': nombre,
                    'telefono': telefono,
                    'direccion': direccion,
                },
            )
            clientes.append(cliente)

        # -------------------------------------------------
        # 3. Productos
        # -------------------------------------------------

        productos_data = [
            ('Torta de chocolate', 'Torta artesanal de chocolate',
             Decimal('24990')),
            ('Torta de vainilla', 'Torta artesanal de vainilla',
             Decimal('21990')),
            ('Cupcakes', 'Caja de cupcakes artesanales',
             Decimal('12990')),
            ('Brownies', 'Porción de brownies de chocolate',
             Decimal('8990')),
            ('Cheesecake', 'Cheesecake artesanal',
             Decimal('26990')),
        ]

        productos = {}

        for nombre, descripcion, precio in productos_data:
            producto, _ = Producto.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'descripcion': descripcion,
                    'precio_base': precio,
                    'activo': True,
                },
            )
            productos[nombre] = producto

        # -------------------------------------------------
        # 4. Insumos y stock inicial
        # -------------------------------------------------

        insumos_data = [
            ('Harina', 'g', Decimal('20000'), Decimal('2000')),
            ('Azúcar', 'g', Decimal('15000'), Decimal('1500')),
            ('Huevos', 'un', Decimal('100'), Decimal('12')),
            ('Mantequilla', 'g', Decimal('10000'), Decimal('1000')),
            ('Chocolate', 'g', Decimal('10000'), Decimal('1000')),
            ('Leche', 'ml', Decimal('10000'), Decimal('1000')),
            ('Crema', 'ml', Decimal('10000'), Decimal('1000')),
            ('Frutillas', 'g', Decimal('5000'), Decimal('500')),
        ]

        insumos = {}

        for nombre, unidad, stock, minimo in insumos_data:
            insumo, _ = Insumo.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'unidad': unidad,
                    'stock_actual': Decimal('0'),
                    'stock_minimo': minimo,
                    'activo': True,
                },
            )

            # No duplicar la carga inicial al ejecutar el comando otra vez.
            referencia = 'Carga inicial DEMO Dulce Arte'

            if not MovimientoInventario.objects.filter(
                insumo=insumo,
                observacion=referencia,
            ).exists():
                insumo.stock_actual += stock
                insumo.save(update_fields=['stock_actual'])

                MovimientoInventario.objects.create(
                    insumo=insumo,
                    tipo='ENTRADA',
                    cantidad=stock,
                    observacion=referencia,
                )

            insumos[nombre] = insumo

        # -------------------------------------------------
        # 5. Recetas y componentes BOM
        # -------------------------------------------------

        recetas_data = {
            'Torta de chocolate': {
                'Harina': 500,
                'Azúcar': 300,
                'Huevos': 4,
                'Mantequilla': 250,
                'Chocolate': 200,
                'Leche': 200,
            },
            'Torta de vainilla': {
                'Harina': 500,
                'Azúcar': 300,
                'Huevos': 4,
                'Mantequilla': 200,
                'Leche': 250,
            },
            'Cupcakes': {
                'Harina': 400,
                'Azúcar': 250,
                'Huevos': 3,
                'Mantequilla': 150,
                'Leche': 200,
            },
            'Brownies': {
                'Harina': 250,
                'Azúcar': 300,
                'Huevos': 3,
                'Mantequilla': 200,
                'Chocolate': 300,
            },
            'Cheesecake': {
                'Harina': 200,
                'Azúcar': 250,
                'Huevos': 3,
                'Mantequilla': 150,
                'Crema': 400,
                'Frutillas': 200,
            },
        }

        for nombre_producto, componentes in recetas_data.items():
            receta, _ = RecetaBOM.objects.get_or_create(
                producto=productos[nombre_producto]
            )

            for nombre_insumo, cantidad in componentes.items():
                DetalleBOM.objects.get_or_create(
                    receta=receta,
                    insumo=insumos[nombre_insumo],
                    defaults={'cantidad': Decimal(str(cantidad))},
                )

        # -------------------------------------------------
        # 6. Pedidos y detalles
        # -------------------------------------------------

        pedidos = []

        for i, cliente in enumerate(clientes):
            producto = list(productos.values())[i]

            referencia = f'DEMO-DULCE-ARTE-PEDIDO-{i + 1:02d}'

            pedido = Pedido.objects.filter(
                observaciones=referencia
            ).first()

            if pedido is None:
                pedido = Pedido.objects.create(
                    cliente=cliente,
                    creado_por=vendedor,
                    fecha_entrega=timezone.localdate() + timedelta(days=i + 1),
                    hora_entrega=time(12 + i, 0),
                    direccion_entrega=cliente.direccion,
                    diseno_personalizado=(
                        'Decoración personalizada de demostración'
                    ),
                    observaciones=referencia,
                )

                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=1,
                    precio_unitario=producto.precio_base,
                    ingredientes_adicionales='Sin ingredientes adicionales',
                    especificaciones='Producto de demostración',
                )

            pedidos.append(pedido)

        # -------------------------------------------------
        # 7. Confirmar tres pedidos
        # -------------------------------------------------

        for pedido in pedidos[:3]:
            if pedido.estado == 'COTIZACION':
                confirmar_pedido(pedido.id, vendedor)

        # -------------------------------------------------
        # 8. Generar órdenes de producción
        # -------------------------------------------------

        ordenes = []

        for pedido in pedidos[:3]:
            orden = OrdenProduccion.objects.get(pedido=pedido)
            ordenes.append(orden)

        # Dos órdenes llegan a LISTO.
        for orden in ordenes[:2]:
            while orden.estado != 'LISTO':
                avanzar_etapa(orden.id)
                orden.refresh_from_db()

        # La tercera queda en preparación.
        if ordenes[2].estado == 'RECIBIDO':
            avanzar_etapa(ordenes[2].id)

        # -------------------------------------------------
        # 9. Despachos
        # -------------------------------------------------

        despachos = []

        for i, pedido in enumerate(pedidos[:2]):
            despacho, _ = Despacho.objects.get_or_create(
                pedido=pedido,
                defaults={
                    'repartidor': repartidor,
                    'direccion': pedido.direccion_entrega,
                    'fecha_entrega': pedido.fecha_entrega,
                    'hora_entrega': pedido.hora_entrega,
                    'orden_ruta': i + 1,
                    'estado': 'PENDIENTE',
                    'observaciones': 'Despacho de demostración',
                },
            )
            despachos.append(despacho)

        # -------------------------------------------------
        # 10. Una entrega de demostración con imagen
        # -------------------------------------------------

        despacho = despachos[0]
        despacho.refresh_from_db()

        if despacho.estado == 'PENDIENTE':
            iniciar_despacho(despacho.id)
            despacho.refresh_from_db()

        if despacho.estado == 'EN_RUTA':
            imagen = Image.new('RGB', (900, 500), 'white')
            dibujo = ImageDraw.Draw(imagen)

            dibujo.text(
                (180, 180),
                'DULCE ARTE - COMPROBANTE DEMO',
                fill='black',
            )
            dibujo.text(
                (250, 240),
                'IMAGEN DE PRUEBA - NO ES UNA ENTREGA REAL',
                fill='black',
            )

            buffer = BytesIO()
            imagen.save(buffer, format='JPEG')

            fotografia = ContentFile(
                buffer.getvalue(),
                name=f'comprobante-demo-{despacho.id}.jpg',
            )

            confirmar_entrega(
                despacho.id,
                fotografia,
                recibido_por='Cliente de demostración',
                observaciones='Comprobante ficticio para demostración académica',
            )

        self.stdout.write(
            self.style.SUCCESS(
                'Datos de demostración creados o verificados correctamente.'
            )
        )

        self.stdout.write('Usuarios de demostración nuevos:')
        self.stdout.write('  vendedor_demo / DulceArteDemo2026!')
        self.stdout.write('  cocina_demo / DulceArteDemo2026!')
        self.stdout.write('  despacho_demo / DulceArteDemo2026!')
