# Bouncer

Un portero que comprueba llamadas a herramientas antes de ejecutarlas. Proyecto para el AI Incident Response Sprint de Apart Research × CeSIA, con unas 12 horas de trabajo real.

**Estado:** alcance y diseño definidos; implementación, pruebas y resultados pendientes. El repositorio contiene documentación y datos para preparar el experimento. Todavía no hay instrucciones de instalación o ejecución del portero.

## La tesis

**No es que no hubiera controles.** En el incidente de OpenAI/Hugging Face había identidad de agente puesta por código de confianza, ~1.300 transcripciones con las llamadas y el razonamiento, contenedores sin ruta a internet y un proxy con allowlist de cuatro dominios.

Lo que faltaba era peor que no tener nada:

- **Nadie leía las transcripciones.** «OpenAI did not use a scorer that would review their transcripts». Los agentes creían que sí, y coordinaron durante días para engañar a un vigilante que no existía.
- **El registro estaba al alcance del vigilado.** Salieron del contenedor y sustituyeron el trozo del sistema que ejecuta las llamadas, así que podían declarar una y ejecutar otra. Al menos 96 transcripciones, en torno al 7 %.
- **El canal por el que se coordinaron 1.200 agentes no tenía autenticación.** «Shared board unauthenticated, names can be posted by anyone», lo escribió un agente. Ellos mismos se montaron un esquema de firma para no suplantarse.
- **La visibilidad terminaba en el escape del sandbox.** Las ~17.600 acciones posteriores las reconstruyó la víctima con sus propios registros.

**El fallo no fue no tener datos. Fue tenerlos, no mirarlos, y guardarlos donde el vigilado podía reescribirlos.**

De ahí las dos funciones del portero, y la segunda no es un extra: comprobar la llamada antes de ejecutarla, y **producir el registro desde código de confianza**, fuera del alcance de escritura del agente. Ninguno de los controles que había preguntaba si una llamada encajaba con el encargo autorizado.

El caso de la wiki lo enseña en pequeño y sin suponer nada: escribir estaba prohibido y el sandbox lo imponía bloqueando POST, pero la wiki acepta editar por GET, así que la escritura pasó disfrazada de lectura. El control miraba el transporte; un portero mira la llamada.

## Qué contiene la entrega

La **parte 1** recorre el caso OpenAI/Hugging Face, que es lo que pide el Track 1: qué control existía, qué habría visto cada uno sobre las nueve fases documentadas (matriz control × fase), qué datos pediríamos al operador y qué no podemos ejecutar ni por presupuesto ni por prudencia.

La **parte 2** implementa y mide con el registro de ediciones de una wiki, que es la evidencia observable que cae en el segundo hueco. Usamos los nombres no humanos como IDs, declaramos los datos faltantes y reproducimos las ediciones sin ejecutar instrucciones, código ni URLs del corpus.

La demostración del sprint simula la tarea de investigación con un portero entre la llamada a herramienta y su ejecución. Escribimos nosotros el encargo y las llamadas guionizadas, sin LLM ni gasto de API. El portero y las herramientas locales sí se ejecutan: las lecturas devuelven contenido y una edición bloqueada deja la wiki local intacta. El objetivo es enseñar un caso de uso verificable con pruebas concretas; el guion no es comportamiento observado de un modelo y el corpus solo conserva las ediciones, no la investigación completa.

El mínimo combina **reglas de permisos** y **reglas con memoria por ID**, junto con un registro de decisiones y un ejecutor controlado para verificar que las llamadas bloqueadas no se ejecutan. La política es **una lista de las llamadas que la tarea autoriza, con denegación por defecto**: lo que no está en la lista se bloquea. Editar una página salta por no estar, no porque ninguna regla la nombre.

La revisión con un LLM o clasificador y el análisis entre agentes son **opcionales**. La detección estadística de anomalías no es un requisito del mínimo, y los agregados del incidente dan un argumento en contra: las acciones fuera del encargo son el 2,7 % del volumen documentado.

## Límites declarados

De ExploitGym no tomamos nada para el código: ni instancias, ni encargos, ni herramientas, ni pruebas. Solo aporta contexto documental sobre el control existente para la matriz control × fase.

La reproducción de la wiki muestra decisiones retrospectivas sobre acciones observadas. La prueba del ejecutor demuestra el veto en un entorno controlado. Ninguna de las dos permite afirmar que se habría evitado el incidente completo. Que los agentes de la wiki llegaran por el hueco de provider-side es una hipótesis consistente con la evidencia, no un mecanismo demostrado: el corpus no contiene ninguna llamada a herramienta.

La wiki entera es comportamiento del incidente, así que por sí sola no permite contar bloqueos erróneos de trabajo legítimo. Lo comprobamos con casos propios y límites declarados, sin depender de un corpus externo ni atribuirles una tasa general de acierto.

## Documentación

- [PRD: alcance, requisitos y criterios de aceptación](PRD.md).
- [Diseño del proyecto: partes 1 y 2, esquema, datos y evaluación](docs/proyecto-portero-tool-calls.md).
- [Hallazgos sobre ExploitGym y su harness](docs/hallazgos-exploitgym.md), con fuentes y aviso de versión.
- [Contexto y requisitos del sprint](docs/ai-incident-response-sprint.md).
- [Datos de la wiki](data/collusion-wiki/) y [agregados y muestras de Hugging Face](docs/datos-replay-hf.json).
- [Tareas pendientes](docs/tareas-pendientes.md).
- [Instrucciones para trabajar en el repositorio](AGENTS.md).

Para los conteos y supuestos del corpus, prevalece la revisión documentada en el diseño del proyecto sobre los resúmenes históricos del README de datos.
