# Bouncer

Un portero que comprueba llamadas a herramientas antes de ejecutarlas. Proyecto para el AI Incident Response Sprint de Apart Research × CeSIA, con unas 12 horas de trabajo real.

**Estado:** alcance y diseño definidos; implementación, pruebas y resultados pendientes. El repositorio contiene documentación y datos para preparar el experimento. Todavía no hay instrucciones de instalación o ejecución del portero.

## La tesis

ExploitGym, el benchmark en el centro del incidente de OpenAI/Hugging Face, aplica tres controles sobre el agente: contenedores sin ruta a internet con un proxy de allowlist de cuatro dominios, un scorer que revisa a posteriori si el agente se salió del camino previsto, y desde v1.1 una lista de denegación de herramientas de recuperación del proveedor en la petición a la API.

**Ninguno de los tres pregunta si una llamada encaja con el encargo autorizado, y ninguno mira las herramientas propias del agente.** Ahí se coloca el portero, y ahí ocurrió el incidente: el canal de coordinación de unos 1.200 agentes fue una caché de paquetes alojada internamente, un recurso alcanzable sobre el que nadie comprobaba la operación.

Y hay una segunda función además de bloquear. No existe ningún dataset público con las acciones de agentes en un incidente real, y donde sí hubo registro, el 7 % estaba falseado porque los agentes sustituyeron parte del sistema que ejecuta las llamadas. Si corres agentes hay que registrar qué acción hizo cada uno y quién la hizo, desde código de confianza y fuera de su alcance de escritura. El portero es ese punto.

## Qué contiene la entrega

La **parte 1** recorre el caso OpenAI/Hugging Face, que es lo que pide el Track 1: qué control existía, qué habría visto cada uno sobre las nueve fases documentadas (matriz control × fase), qué datos pediríamos al operador y qué no podemos ejecutar ni por presupuesto ni por prudencia.

La **parte 2** implementa y mide con el registro de ediciones de una wiki, que es la evidencia observable que cae en el segundo hueco. Usamos los nombres no humanos como IDs, declaramos los datos faltantes y reproducimos las ediciones sin ejecutar instrucciones, código ni URLs del corpus.

El mínimo combina **reglas de permisos** y **reglas con memoria por ID**, junto con un registro de decisiones y un ejecutor controlado para verificar que las llamadas bloqueadas no se ejecutan. Los dos escenarios de permisos que comparamos, estricto y permisivo, se toman de la configuración publicada del harness, no se inventan.

La revisión con un LLM o clasificador y el análisis entre agentes son **opcionales**. La detección estadística de anomalías no es un requisito del mínimo, y los agregados del incidente dan un argumento en contra: las acciones fuera del encargo son el 2,7 % del volumen documentado.

## Límites declarados

No ejecutamos ExploitGym: exige infraestructura de evaluación de capacidad peligrosa y no cabe en el presupuesto. Sus instancias se usan solo como encargo autorizado de pruebas propias.

La reproducción de la wiki muestra decisiones retrospectivas sobre acciones observadas. La prueba del ejecutor demuestra el veto en un entorno controlado. Ninguna de las dos permite afirmar que se habría evitado el incidente completo. Que los agentes de la wiki llegaran por el hueco de provider-side es una hipótesis consistente con la evidencia, no un mecanismo demostrado: el corpus no contiene ninguna llamada a herramienta.

Falta el grupo de control: ejemplos de agentes trabajando bien, para contar cuántos bloquea el portero por error. La wiki entera es comportamiento del incidente, así que por sí sola no permite medir eso. Si no aparece un conjunto público adecuado, se usan casos propios con límites declarados.

## Documentación

- [PRD: alcance, requisitos y criterios de aceptación](.codex/plans/PRD.md).
- [Diseño del proyecto: partes 1 y 2, esquema, datos y evaluación](docs/proyecto-portero-tool-calls.md).
- [Hallazgos sobre ExploitGym y su harness](docs/hallazgos-exploitgym.md), con fuentes y aviso de versión.
- [Contexto y requisitos del sprint](docs/ai-incident-response-sprint.md).
- [Datos de la wiki](data/collusion-wiki/) y [agregados y muestras de Hugging Face](docs/datos-replay-hf.json).
- [Tareas pendientes](docs/tareas-pendientes.md).
- [Instrucciones para trabajar en el repositorio](AGENTS.md).

Para los conteos y supuestos del corpus, prevalece la revisión documentada en el diseño del proyecto sobre los resúmenes históricos del README de datos.
