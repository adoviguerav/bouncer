# Bouncer

Un portero que comprueba llamadas a herramientas antes de ejecutarlas. Proyecto para el AI Incident Response Sprint de Apart Research × CeSIA, con unas 12 horas de trabajo real.

**Estado:** alcance y diseño definidos; fase 1 (dataset único) implementada y verificada; portero, memoria, demo y resultados pendientes. Todavía no hay instrucciones de ejecución del portero.

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

La **parte 2** prepara un dataset único con el registro de ediciones de una wiki, implementa el portero y demuestra su funcionamiento con herramientas locales. Usamos los nombres no humanos como IDs, declaramos los datos faltantes y reproducimos las ediciones sin ejecutar instrucciones, código ni URLs del corpus.

La demostración del sprint simula la tarea de investigación con un portero entre la llamada a herramienta y su ejecución. Escribimos nosotros el encargo y las llamadas guionizadas, sin LLM ni gasto de API. El portero y las herramientas locales sí se ejecutan: las lecturas devuelven contenido y una edición bloqueada deja la wiki local intacta. El objetivo es enseñar un caso de uso verificable con pruebas concretas; el guion no es comportamiento observado de un modelo y el corpus solo conserva las ediciones, no la investigación completa.

El mínimo combina **reglas de permisos** y **reglas con memoria por ID**, junto con un registro de decisiones y un ejecutor controlado para verificar que las llamadas bloqueadas no se ejecutan. La política es **una lista de las llamadas que la tarea autoriza, con denegación por defecto**: lo que no está en la lista se bloquea. Editar una página salta por no estar, no porque ninguna regla la nombre.

La revisión con un LLM o clasificador y el análisis entre agentes son **opcionales**. La detección estadística de anomalías no es un requisito del mínimo, y los agregados del incidente dan un argumento en contra: las acciones fuera del encargo son el 2,7 % del volumen documentado.

## Fases de implementación

El [PRD](PRD.md), en su sección 11, define las tareas y el cierre de cada fase. La fase 1 está hecha; las demás, pendientes:

1. **Dataset único y limpio.** Hecho: ver [Preparar el dataset](#preparar-el-dataset). Un archivo JSONL tabular, con una fila por revisión utilizada, los campos necesarios para analizarla y su procedencia. Se inspecciona como tabla sin volver a unir los archivos originales; el resumen de limpieza explica las exclusiones.
2. **Escenario de investigación propio.** Preparar páginas, preguntas y estado local; escribir la política y los guiones con las cinco operaciones legítimas y una edición prohibida. Fijar una restricción con memoria y sus resultados esperados antes de medirla.
3. **Portero y ejecución controlada.** Comprobar cada llamada antes de invocar la herramienta, asignar identidad y política desde código de confianza y registrar la decisión y el resultado. Probar que una lectura funciona y que una edición bloqueada no produce efecto.
4. **Memoria por ejecución y agente.** Aplicar la restricción de secuencia definida en el escenario. Comprobar límites, intentos simultáneos y separación de historiales.
5. **Demo, reproducción y resultados.** Ejecutar los guiones sin LLM y pasar el dataset histórico por el portero sin ejecutar su contenido. Comparar permisos solos frente a permisos con memoria, producir tablas y tiempos, y verificar los comandos para repetirlo.

Las pruebas acompañan cada fase. El informe del sprint y la matriz de Hugging Face siguen siendo entregables obligatorios; son trabajo documental separado de estas fases técnicas.

## Preparar el dataset

Requiere Python 3.11+ y [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run python -m bouncer.prepare --output-dir data/prepared/wiki
uv run pytest -q tests/test_prepare.py
```

**Entradas:** `data/collusion-wiki/revisions.jsonl.gz` y `labels.jsonl.gz`. No se modifican; `cleaning.json` registra sus SHA-256.

**Salidas** en `data/prepared/wiki/`, versionadas en el repositorio:

- `events.jsonl`: 13.661 filas, una por revisión utilizada, ordenadas por `time` con desempate por `rev_id` (el desempate es técnico, no afirma orden real dentro del mismo segundo). Columnas: `rev_id`, `source_ref` (fichero:línea de origen), `agent_id` (el `label` literal, sin fusionar nombres), `time`, `time_grade`, `uncertainty_seconds`, `page_key`, `seq`, `body` (cuerpo completo; `""` es una página vaciada, no un dato ausente), `request_action` (`null` cuando el original no lo trae), `operation` (siempre `wiki.edit`, adaptación declarada) y `provenance` (qué es observado, adaptado o desconocido en esa fila).
- `cleaning.json`: entrada 14.591 = 31 humanos (`is_human_handle` en `labels`) + 899 sin nombre + 13.661 utilizadas. Recuperadas 0: ninguna fila sin nombre tiene `related_event_id`. 3.099 IDs, 74 cuerpos vacíos, 74 sin `request_action`.

Dos ejecuciones sobre los mismos originales producen ficheros idénticos byte a byte. El dataset se carga solo:

```python
import pandas as pd
df = pd.read_json("data/prepared/wiki/events.jsonl", lines=True)
```

No contiene decisiones, política ni guiones propios; el ID de reproducción lo asignará el ejecutor en fases posteriores.

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
