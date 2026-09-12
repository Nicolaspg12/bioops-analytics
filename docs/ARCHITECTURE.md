# Decisiones técnicas

1. **SQLite** mantiene la demo reproducible sin servicios adicionales. La carga realiza escrituras dentro de una sola transacción. Para escrituras concurrentes sostenidas, migraría a PostgreSQL con migraciones y pruebas de carga.
2. **Clave de negocio `asset_id`** permite upserts idempotentes. No existe borrado implícito: los equipos ausentes de un CSV permanecen en la base.
3. **Validación antes del upsert** separa errores de fila de errores estructurales. No se guardan las filas rechazadas completas: solo el número y el motivo, reduciendo retención innecesaria de datos.
4. **Reglas deterministas** facilitan comprobar los indicadores sin un modelo predictivo opaco. La criticidad procede del CSV, no se infiere.
5. **Frontend sin dependencias** reduce pasos de instalación. El contenido importado se inserta con `textContent`, no se interpreta como HTML.
6. **Fecha de corte limitada:** se almacena solo el último servicio conocido. Un servicio posterior al corte se marca sin historial; para análisis histórico real se necesita una tabla de eventos.

## Esquema

- `assets`: identidad, descripción, ubicación, último servicio, intervalo y criticidad.
- `runs`: fecha UTC y conteos de cada importación.
- `rejections`: referencia a la carga, línea del CSV y motivo de rechazo.

## Límites

Máximo 2 MB y 10.000 filas por solicitud; un fallo de cabecera no genera una carga. No hay autenticación, gestión multiusuario, calendario laboral ni validación de normativa biomédica. La API se ejecuta por defecto en loopback. Para despliegue público hacen falta autenticación, límites de concurrencia, observabilidad, copias de seguridad y HTTPS.
