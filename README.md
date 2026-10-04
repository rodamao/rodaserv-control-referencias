
# RODASERV CONTROL DE REFERENCIAS V3

Aplicación Streamlit para trabajar desde celulares con un equipo comercial/bodega.

## Incluye

- Reporte de **Agotados**
- Reporte de **Referencia nueva**
- Usuario, fecha y hora automáticos
- Marca, aplicación, cantidad sugerida, cliente y observaciones
- Flujo de estados:
  1. Reportado
  2. En revisión
  3. Validado
  4. Gestión de compra
  5. Solucionado
  6. Descartado
- Dashboard de avance
- Seguimiento individual por referencia
- Filtros por tipo, estado y usuario
- Exportación a Excel con hojas REPORTES, PENDIENTES, AGOTADOS y NUEVAS
- 5 usuarios demo
- Diseño pensado para celular

## Usuarios demo

- admin / admin123
- bodega / bodega123
- vendedor1 / vendor1
- vendedor2 / vendor2
- vendedor3 / vendor3

IMPORTANTE: para producción, cambie las contraseñas usando Streamlit Secrets.

## Opción recomendada para trabajo en equipo por Internet: Google Sheets

La app puede usar una hoja de Google Sheets como base central. Todos los celulares consultan y actualizan la misma información.

### 1. Crear la hoja

Cree un Google Sheet y una pestaña llamada `REPORTES`.

La aplicación crea los encabezados si la pestaña está vacía.

### 2. Crear una cuenta de servicio de Google Cloud

Habilite Google Sheets API y Google Drive API, cree una Service Account y descargue su JSON.

Comparta el Google Sheet con el correo de la Service Account como Editor.

### 3. Configurar Streamlit Secrets

En Streamlit Community Cloud, agregue:

[users.admin]
password = "CAMBIAR"
role = "Administrador"
name = "Administrador"

[users.bodega]
password = "CAMBIAR"
role = "Bodega"
name = "Bodega"

[users.vendedor1]
password = "CAMBIAR"
role = "Vendedor"
name = "Vendedor 1"

[users.vendedor2]
password = "CAMBIAR"
role = "Vendedor"
name = "Vendedor 2"

[users.vendedor3]
password = "CAMBIAR"
role = "Vendedor"
name = "Vendedor 3"

spreadsheet_id = "ID_DEL_GOOGLE_SHEET"
worksheet_name = "REPORTES"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."

## Publicar

1. Suba estos archivos a un repositorio de GitHub.
2. Entre a Streamlit Community Cloud.
3. Cree una app y seleccione `app.py`.
4. Pegue los Secrets.
5. Publique.
6. Comparta la URL con el equipo.

La aplicación funciona en el navegador del celular; no necesita instalar APK.

## Nota de arquitectura

Para un equipo que trabaja simultáneamente por Internet, no se debe depender de un CSV local como base central. Google Sheets es el modo incluido en esta versión para mantener un registro compartido.

Para una siguiente etapa empresarial se puede migrar el mismo esquema a Supabase/PostgreSQL y agregar auditoría completa, permisos por vendedor, fotografías, notificaciones y conexión con el maestro de referencias.
