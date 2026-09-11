# Bouncer

Un portero que comprueba llamadas a herramientas antes de ejecutarlas. Proyecto para el AI Incident Response Sprint de Apart Research × CeSIA, con unas 12 horas de trabajo real.

**Estado:** alcance y diseño definidos; implementación, pruebas y resultados pendientes. El repositorio contiene documentación y datos para preparar el experimento. Todavía no hay instrucciones de instalación o ejecución del portero.

## Qué implementamos ahora

La **parte A** prueba la idea con el registro de ediciones de una wiki. Usamos los nombres no humanos como IDs, declaramos los datos faltantes y reproducimos las ediciones sin ejecutar instrucciones, código ni URLs del corpus.

El mínimo combina **reglas de permisos** y **reglas con memoria por ID**, junto con un registro de decisiones y un ejecutor controlado para verificar que las llamadas bloqueadas no se ejecutan. Las políticas del experimento son explícitas: no conocemos los encargos originales de todos los agentes.

La revisión con un LLM o clasificador y el análisis entre agentes son **opcionales**. El análisis colectivo aporta señales junto al individual; no es un filtro posterior al modelo. La detección estadística de anomalías tampoco es un requisito del mínimo.

## Qué queda para después

La **parte B** explica cómo aplicaríamos y evaluaríamos el sistema con IDs asignados por el ejecutor, tareas y permisos conocidos, llamadas originales y resultados. El caso OpenAI/Hugging Face motiva esta propuesta; los agregados y muestras disponibles no equivalen a esas trayectorias completas.

La reproducción de la wiki muestra decisiones retrospectivas sobre acciones observadas. La prueba del ejecutor demuestra el veto en un entorno controlado. Ninguna de las dos permite afirmar que se habría evitado el incidente completo.

## Documentación

- [PRD: alcance, requisitos y criterios de aceptación](.codex/plans/PRD.md).
- [Diseño del proyecto: partes A y B, esquema, datos y evaluación](docs/proyecto-portero-tool-calls.md).
- [Contexto y requisitos del sprint](docs/ai-incident-response-sprint.md).
- [Datos de la wiki](data/collusion-wiki/) y [agregados y muestras de Hugging Face](docs/datos-replay-hf.json).
- [Instrucciones para trabajar en el repositorio](AGENTS.md).

Para los conteos y supuestos del corpus, prevalece la revisión documentada en el diseño del proyecto sobre los resúmenes históricos del README de datos. La carga legítima comparable todavía está pendiente de selección; si no se obtiene dentro del plazo, se usarán casos propios con límites declarados.
