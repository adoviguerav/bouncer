# Bouncer

Un portero que comprueba llamadas a herramientas antes de ejecutarlas. Proyecto para el AI Incident Response Sprint de Apart Research × CeSIA, con unas 12 horas de trabajo real.

**Estado:** alcance y diseño definidos; implementación, pruebas y resultados pendientes. El repositorio contiene documentación y datos para preparar el experimento. Todavía no hay instrucciones de instalación o ejecución del portero.

## La tesis

El control que hoy se despliega sobre agentes en este dominio es perimetral o retrospectivo. ExploitGym, el benchmark en el centro del incidente de OpenAI/Hugging Face, aísla al agente en contenedores sin ruta a internet y hace pasar su tráfico por un proxy con allowlist de cuatro dominios. En el punto de la llamada a herramienta no hay nada: ni comprobación, ni registro de acciones del agente.

Ese control tiene dos huecos y ninguno es un descuido. La fase de instalación es allow-all, porque los repositorios de paquetes no se pueden enumerar por adelantado, y es por donde pasó el incidente de julio. Y el tráfico del lado del proveedor, búsqueda web y MCP, no pasa por el proxy en absoluto: lo dice su propia documentación. El portero se coloca justo ahí.

## Qué contiene la entrega

La **parte 1** recorre el caso OpenAI/Hugging Face, que es lo que pide el Track 1: qué control existía, qué habría visto cada uno sobre las nueve fases documentadas (matriz control × fase), qué datos pediríamos al operador y qué no podemos ejecutar ni por presupuesto ni por prudencia.

La **parte 2** implementa y mide con el registro de ediciones de una wiki, que es la evidencia observable que cae en el segundo hueco. Usamos los nombres no humanos como IDs, declaramos los datos faltantes y reproducimos las ediciones sin ejecutar instrucciones, código ni URLs del corpus.

El mínimo combina **reglas de permisos** y **reglas con memoria por ID**, junto con un registro de decisiones y un ejecutor controlado para verificar que las llamadas bloqueadas no se ejecutan. Los dos escenarios de permisos que comparamos, estricto y permisivo, se toman de la configuración publicada del harness, no se inventan.

La revisión con un LLM o clasificador y el análisis entre agentes son **opcionales**. La detección estadística de anomalías no es un requisito del mínimo, y los agregados del incidente dan un argumento en contra: las acciones fuera del encargo son el 2,7 % del volumen documentado.

## Límites declarados

No ejecutamos ExploitGym: exige infraestructura de evaluación de capacidad peligrosa y no cabe en el presupuesto. Sus instancias se usan solo como encargo autorizado de pruebas propias.

La reproducción de la wiki muestra decisiones retrospectivas sobre acciones observadas. La prueba del ejecutor demuestra el veto en un entorno controlado. Ninguna de las dos permite afirmar que se habría evitado el incidente completo. Que los agentes de la wiki llegaran por el hueco de provider-side es una hipótesis consistente con la evidencia, no un mecanismo demostrado: el corpus no contiene ninguna llamada a herramienta.

La carga legítima comparable todavía está pendiente de selección; si no se obtiene dentro del plazo, se usarán casos propios con límites declarados.

## Documentación

- [PRD: alcance, requisitos y criterios de aceptación](.codex/plans/PRD.md).
- [Diseño del proyecto: partes 1 y 2, esquema, datos y evaluación](docs/proyecto-portero-tool-calls.md).
- [Hallazgos sobre ExploitGym y su harness](docs/hallazgos-exploitgym.md), con fuentes y aviso de versión.
- [Contexto y requisitos del sprint](docs/ai-incident-response-sprint.md).
- [Datos de la wiki](data/collusion-wiki/) y [agregados y muestras de Hugging Face](docs/datos-replay-hf.json).
- [Tareas pendientes](docs/tareas-pendientes.md).
- [Instrucciones para trabajar en el repositorio](AGENTS.md).

Para los conteos y supuestos del corpus, prevalece la revisión documentada en el diseño del proyecto sobre los resúmenes históricos del README de datos.
