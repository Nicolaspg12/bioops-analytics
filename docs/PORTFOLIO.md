# Cómo presentar BioOps en una entrevista

## Demo de 3 minutos

1. Inicia la API y carga la demo. Explica la relación entre último servicio, intervalo y fecha de corte.
2. Filtra por sede y muestra los equipos vencidos de criticidad alta.
3. Carga de nuevo la demo: los registros no se duplican. Abre la bitácora para mostrar los conteos.
4. Importa `samples/invalid_rows.csv` y abre los motivos de rechazo.
5. Exporta CSV y abre Swagger. Muestra una prueba de la regla de vencimiento.

## Texto breve para el portafolio

“BioOps Analytics es una aplicación de portafolio en Python y FastAPI que valida inventarios CSV, realiza cargas idempotentes en SQLite y presenta indicadores de mantenimiento. Incluye bitácora de calidad, exportación, pruebas y configuración Docker.”

## Preguntas para preparar

- ¿Por qué un upsert necesita una clave de negocio estable?
- ¿Qué ocurre si falla una escritura a mitad de la carga?
- ¿Por qué el cumplimiento incluye equipos que vencen dentro de 30 días?
- ¿Qué cambia al pasar de SQLite a PostgreSQL?
- ¿Qué estructura permitiría reconstruir el historial de mantenimientos?

Este es un proyecto nuevo de portafolio construido con asistencia de IA. Revisa y comprende el código antes de presentarlo. No atribuyas uso empresarial, ahorro de costos o impacto operativo que no se haya medido.
