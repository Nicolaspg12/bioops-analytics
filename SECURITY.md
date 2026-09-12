# Seguridad de la demostración local

## Protecciones

- El servidor debe iniciarse en `127.0.0.1`; Docker publica el puerto solo en loopback.
- Se aceptan únicamente los nombres de host `localhost`, `127.0.0.1` y `[::1]`.
- Las solicitudes de navegador con origen externo, origen opaco (`null`) o `Sec-Fetch-Site: cross-site` se rechazan antes de ejecutar las rutas. Esto reduce el riesgo de peticiones de otra página hacia la API local y de DNS rebinding.
- La interfaz no permite scripts externos, objetos embebidos ni ser presentada dentro de un iframe. La documentación Swagger conserva su renderer habitual con recursos externos.
- Respuestas con `nosniff`, sin envío de Referer y sin caché. CSV validado y consultas SQL parametrizadas.
- No contiene claves de OpenAI, integraciones de facturación ni procesos de IA en segundo plano.

## Revisión del 12 de septiembre de 2026

Antes de la corrección, una solicitud simulada desde un origen externo podía activar `/api/demo`, y un Host externo era aceptado. Se añadieron controles de Host/origen y pruebas que verifican el rechazo sin modificar la base.

La revisión de patrones de credenciales en el código y el historial Git no encontró coincidencias de claves privadas, tokens GitHub/OpenAI/AWS ni URLs con contraseña. No se versionaron el CV, archivos `.env` ni la base de datos. No había hooks Git activos.

`pip-audit 2.10.1 -r requirements-dev.txt` no encontró vulnerabilidades conocidas en las dependencias resueltas el día de la revisión. Esto no garantiza ausencia de vulnerabilidades desconocidas. La suite completa pasó 13 pruebas.

## Límites

Estos controles no sustituyen autenticación ni aislamiento entre usuarios del mismo equipo. Un proceso local con acceso al equipo puede invocar la API. No está diseñado para Internet, redes compartidas o datos biomédicos reales. La revisión cubre este proyecto, no las sesiones, la autenticación multifactor ni la facturación de las cuentas personales.

El repositorio sigue siendo público bajo MIT: terceros pueden copiar y reutilizar el código según la licencia. No publiques credenciales ni información confidencial en archivos, issues o comentarios.
