# Validación realizada

Fecha: 2026-09-12. Entorno local: Windows, Python 3.12.

- `python -m pytest -q`: **4 pruebas aprobadas**.
- Idempotencia, actualización por ID, duplicados dentro del CSV y persistencia de rechazos.
- Límites de fechas, corte anterior al último servicio y vencimiento al día siguiente.
- API: base vacía, demo, filtro por sede, exportación filtrada, CSV inválido, UTF-8 inválido, límite de tamaño y parámetros inválidos.
- Exportación con neutralización de fórmulas y filtro SQL parametrizado.
- `node --check app/static/app.js`: sintaxis válida.
- Navegador: carga de 24 equipos, 6 vencidos, 8 próximos y 75 % de cumplimiento. Filtro Sede Norte: 8 equipos. Búsqueda BIO-001: un resultado.
- Captura de la aplicación incluida en `dashboard.png`.

La suite emite avisos de deprecación de Starlette/httpx y AnyIO; no son fallos de las pruebas. GitHub Actions incluye la ejecución en Linux. Docker no estaba instalado en el entorno de creación; su imagen no se construyó localmente. No se realizaron pruebas de carga ni un despliegue de producción.
