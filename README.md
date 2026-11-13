# Dulce Arte

Sistema web de gestión para una pastelería artesanal. Permite
administrar clientes y productos, registrar pedidos personalizados,
controlar el inventario de ingredientes y coordinar la producción y los
despachos.

## Acceso al sistema

-   **Aplicación:** https://backendeva3gb.duckdns.org/  https://54.90.241.164/
-   **Panel de administración de Django:**
    https://backendeva3gb.duckdns.org/admin/

El acceso a las secciones del sistema depende del rol asignado a cada
usuario.

## Funcionalidades

### Gestión de usuarios y permisos

El sistema utiliza un modelo de usuario personalizado y controla el
acceso según los siguientes roles:

-   **Administrador:** administración general del sistema.
-   **Vendedor:** registro y gestión de clientes y pedidos.
-   **Cocina:** seguimiento y avance de las órdenes de producción.
-   **Despacho:** gestión de entregas y registro de comprobantes.

### Clientes y pedidos

-   Registro y consulta de clientes.
-   Creación de pedidos con fecha y hora de entrega.
-   Registro de dirección de entrega, diseño personalizado y
    observaciones.
-   Incorporación de uno o más productos por pedido.
-   Registro de cantidades, precios unitarios, ingredientes adicionales
    y especificaciones.
-   Confirmación de pedidos y consulta de su estado.

### Inventario

-   Administración de ingredientes e insumos.
-   Definición de los ingredientes requeridos para elaborar productos.
-   Control de existencias mediante movimientos de inventario.
-   Descuento de ingredientes al confirmar un pedido, de acuerdo con su
    composición.
-   Validación de disponibilidad para evitar confirmar pedidos sin
    existencias suficientes.

### Producción

El módulo de producción presenta las órdenes en un tablero Kanban con
las siguientes etapas:

1.  Recibido.
2.  En preparación.
3.  Horneado y decorado.
4.  Control de calidad.
5.  Listo.

El personal de cocina puede avanzar las órdenes entre etapas. Una vez
que un pedido está listo, puede marcarse como entregado desde el
tablero. Los pedidos entregados dejan de aparecer en el Kanban, pero se
mantienen registrados en la base de datos.

### Despachos

El módulo de despachos permite gestionar la entrega de pedidos que han
completado la producción y registrar comprobantes de entrega, como
fotografías.

## Tecnologías utilizadas

-   **Backend:** Python y Django.
-   **API:** Django REST Framework.
-   **Base de datos:** PostgreSQL.
-   **Servidor de aplicaciones:** Gunicorn.
-   **Servidor web y proxy inverso:** Nginx.
-   **Despliegue:** máquina virtual Ubuntu en AWS EC2.
-   **Dominio:** DuckDNS.
-   **Certificado HTTPS:** Let's Encrypt / Certbot.

## Estructura del proyecto

Las principales aplicaciones Django son:

  -----------------------------------------------------------------------
  Aplicación                          Responsabilidad
  ----------------------------------- -----------------------------------
  `usuarios`                          Usuarios, autenticación y roles.

  `pedidos`                           Clientes, productos, pedidos y
                                      detalles de pedido.

  `inventario`                        Ingredientes, existencias y
                                      movimientos de inventario.

  `produccion`                        Órdenes de producción y etapas del
                                      Kanban.

  `despachos`                         Gestión de despachos y comprobantes
                                      de entrega.

  `web`                               Vistas, formularios, plantillas e
                                      interfaz web.

  `config`                            Configuración principal del
                                      proyecto y sus URL.
  -----------------------------------------------------------------------

## Instalación en entorno de desarrollo

### Requisitos

-   Python 3.14 o compatible con las dependencias del proyecto.
-   PostgreSQL.
-   Git.

### 1. Clonar el repositorio

``` bash
git clone <URL_DEL_REPOSITORIO>
cd <DIRECTORIO_DEL_PROYECTO>
```

### 2. Crear y activar el entorno virtual

``` bash
python -m venv .venv
```

En Linux:

``` bash
source .venv/bin/activate
```

En Windows:

``` powershell
.venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

``` bash
pip install -r requirements.txt
```

### 4. Configurar las variables de entorno

Crear un archivo `.env` en el directorio del proyecto y definir los
valores requeridos por `config/settings.py`. Como mínimo, configurar la
clave secreta de Django, el modo de depuración, los hosts permitidos y
los datos de conexión a PostgreSQL.

No subir el archivo `.env` al repositorio. Las credenciales y claves
privadas deben mantenerse fuera del control de versiones.

### 5. Preparar la base de datos

Crear en PostgreSQL una base de datos y un usuario con permisos sobre
ella. Configurar sus credenciales en el archivo `.env`.

Luego ejecutar:

``` bash
python manage.py migrate
```

### 6. Crear un usuario administrador

``` bash
python manage.py createsuperuser
```

### 7. Iniciar el servidor de desarrollo

``` bash
python manage.py runserver
```

La aplicación estará disponible normalmente en `http://127.0.0.1:8000/`.

## Despliegue

La versión de producción está desplegada en una máquina virtual Ubuntu
sobre AWS EC2.

La arquitectura de despliegue utiliza:

-   **Nginx** para recibir las solicitudes HTTP/HTTPS y servir los
    archivos estáticos.
-   **Gunicorn** para ejecutar la aplicación Django.
-   **systemd** para administrar el servicio de Gunicorn.
-   **PostgreSQL** como base de datos.
-   **DuckDNS** para asociar el dominio a la instancia.
-   **Certbot** para gestionar el certificado HTTPS.

El servicio de aplicación se administra con:

``` bash
sudo systemctl status dulce-arte
sudo systemctl restart dulce-arte
sudo journalctl -u dulce-arte -n 100 --no-pager
```

Después de actualizar el código en producción, aplicar las migraciones
cuando corresponda y reiniciar el servicio:

``` bash
python manage.py migrate
sudo systemctl restart dulce-arte
```

Los comandos deben ejecutarse desde el directorio del proyecto y
utilizando el entorno virtual configurado para producción.

## Consideraciones de seguridad

-   Mantener `DEBUG=False` en producción.
-   Configurar correctamente `ALLOWED_HOSTS` y los orígenes HTTPS según
    el entorno.
-   No publicar el archivo `.env`, contraseñas, claves secretas ni
    credenciales de base de datos.
-   Utilizar HTTPS para acceder al sistema.
-   Asignar a cada usuario únicamente el rol y los permisos que
    necesita.

## Estado del proyecto

Proyecto académico de backend orientado a la gestión integral de pedidos
de una pastelería artesanal, desde la cotización y confirmación hasta la
producción y entrega.
