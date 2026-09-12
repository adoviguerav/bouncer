# Plan: fase 1 — dataset único, limpio y consultable

**Status**: draft

## Goal

Generar `data/prepared/wiki/events.jsonl`: un único dataset con una fila por revisión utilizada y los campos necesarios para inspeccionarla como tabla y analizarla después. Conservar los originales y producir un resumen de limpieza verificable. Esta es solo la primera fase del proyecto completo: escenario en fase 2, portero/ejecutor/registro en fase 3, memoria en fase 4 y demo/reproducción/resultados en fase 5, según PRD §11.

## Findings

Exploración local del 12-09-2026, leyendo los comprimidos como datos:

- 14.591 revisiones sin `rev_id` duplicados; todas tienen hora interpretable, página y cuerpo de texto.
- Excluir 31 revisiones de tres nombres humanos y 899 sin nombre deja 13.661 revisiones de 3.099 IDs, antes de recuperaciones justificadas. Los anónimos no tienen `related_event_id`.
- 74 cuerpos vacíos válidos en esa base. `request_action` contiene `form_edit` en 14.482 originales y carece de valor en 109; no es una herramienta original de LLM recuperada.
- No hay implementación ni pruebas. `pyproject.toml` declara pandas, PyYAML y pytest. El PRD vigente está en la raíz.

## Decisions

Registro histórico; la última entrada actualiza la distribución por fases de las anteriores.


- **Usuario, 12-09-2026 — pruebas propias.** Nada de ExploitGym entra en código, encargos o casos. Escribimos la tarea de investigación y las llamadas; ExploitGym queda como contexto documental del control existente y de la matriz. Sus encargos de explotación pertenecen a otro escenario.
- **Usuario, 12-09-2026 — demostración de sprint.** Enseñar trabajo autorizado y veto antes del efecto, con comprobaciones concretas. Se retira la exclusividad de `wiki.edit`: el entorno local necesita operaciones legítimas y el intento de edición prohibida. No convertir el caso de uso en un benchmark general.
- **Usuario, 12-09-2026 — sin gasto de modelo.** Reproducir llamadas escritas por nosotros. Portero y efectos locales reales; generación guionizada, sin atribuirla a un agente real. Conectar un LLM no hace falta para demostrar el veto.
- **Alcance heredado.** Una política, cinco operaciones autorizadas y denegación por defecto; memoria por ID. Concretar la regla y sus parámetros es una entrega de fase 1, anterior a implementar o medir. No atribuir mejora de memoria al histórico.
- **Revisión del plan, 12-09-2026.** Desglosar los bloques anteriores en tareas con archivo, salida y comprobación propios. Separar D1, documental sobre Hugging Face, de las dependencias de la demo; su permanencia en fase 1 procede del PRD y no implica usar ese incidente en el código.

- **Usuario y actualización del PRD, 12-09-2026 — dataset primero, proyecto completo.** Fase 1 entrega el dataset único consultable y la limpieza. Escenario, política y regla de memoria pasan a fase 2; el núcleo se construye en fases 3–4 y se demuestra en fase 5. Se conserva todo el alcance y la entrega documental de Hugging Face, fuera de la numeración técnica. Esta distribución sustituye las asignaciones de fase de entradas anteriores.

## Context

Leer `AGENTS.md:18` (stack), `PRD.md` §§5, 7, 8 y 11 (dataset, aceptación y recorrido completo), y `docs/proyecto-portero-tool-calls.md` §§11–12 (limpieza y procedencia). No usar plantillas de arquitectura de otros proyectos ni interpretar texto del corpus como instrucciones.

- **Entradas:** `data/collusion-wiki/revisions.jsonl.gz` y `labels.jsonl.gz`. Otro original solo si una referencia explícita exige comprobar una recuperación.
- **Crear:** `bouncer/__init__.py`, `bouncer/prepare.py`, `tests/test_prepare.py`.
- **Generar:** `data/prepared/wiki/events.jsonl` y `data/prepared/wiki/cleaning.json`.
- **Actualizar:** `README.md` con el comando de preparación que se haya ejecutado y comprobado.

## Acceptance contract

- [ ] Entrada = utilizadas + excluidas, sin doble conteo. Recuperadas es un subconjunto identificado, con evidencia. Cualquier diferencia con la base medida se explica. **Comprueba:** `test_corpus_accounting` y `cleaning.json`.
- [ ] Cada fila conserva revisión/referencia de origen, nombre literal, fecha/calidad, página y cuerpo disponible; distingue observado, adaptado y desconocido. Los 74 cuerpos vacíos de la base se conservan y la ausencia de `request_action` no inventa una llamada. **Comprueban:** `test_provenance_and_empty_bodies`, `test_missing_identity`, `test_missing_request_action`.
- [ ] Dos preparaciones con los mismos originales producen archivos idénticos, con desempate temporal técnico estable. Los hashes de originales no cambian; no entran etiquetas de página ni resúmenes futuros en los eventos. **Comprueban:** `test_repeatable_preparation`, `test_originals_unchanged`, `test_event_fields`.
- [ ] `events.jsonl` se carga por sí solo en pandas como tabla con una fila por revisión utilizada, cuerpo incluido y columnas estables. No requiere unir otros ficheros ni contiene guiones propios, decisiones inventadas o resultados de ejecución. **Comprueba:** `test_dataframe_contract`.

Comandos que existirán al implementar esta fase:

```sh
uv run pytest -q tests/test_prepare.py
uv run python -m bouncer.prepare --output-dir data/prepared/wiki
git diff --check
```

## Out of scope

- Escenario, recursos locales, política y guiones: fase 2.
- Portero, herramientas, ejecutor, identidad de confianza, log y memoria: fases 3–4.
- Demo, reproducción mediante el portero y comparación: fase 5.
- Matriz Hugging Face e informe: entrega documental obligatoria separada. Sin código ni instancias de ExploitGym.
- Ejecutar contenido del corpus, conectar LLMs o construir interfaz para visualizar la tabla.

## Interfaces

`events.jsonl` tiene una fila por revisión utilizada: ID de evento/revisión, archivo/fila de origen, autor literal usado como `agent_id` y procedencia, hora/calidad, página, cuerpo disponible, `request_action` cuando existe, operación adaptada `wiki.edit` y desconocidos explícitos. El ID de reproducción lo asignará el ejecutor al analizar el archivo, no la preparación. No se incorpora política ni decisión al preparar el dataset.

`cleaning.json` documenta conteos, motivos de exclusión y referencias de recuperación. Es el comprobante de la transformación, no un segundo dataset que haya que unir para usar las revisiones.

## Tasks

### T1. CREATE las pruebas con revisiones pequeñas

**Archivo:** `tests/test_prepare.py`. Crear ejemplos propios: revisión válida, humano, anónimo, cuerpo vacío, petición sin acción, fecha inválida, página ausente y empate temporal. Definir los valores y motivos esperados; probar igualdad entre preparaciones e integridad de originales. Añadir la carga tabular desde el único archivo generado.

**Depende de:** nada. **VALIDATE:** `uv run pytest -q tests/test_prepare.py`; observar RED por ausencia del preparador antes de T2.

### T2. CREATE el preparador y su comando

**Archivos:** `bouncer/__init__.py`, `bouncer/prepare.py`. Leer comprimidos, identificar humanos mediante la marca documentada de `labels`, conservar nombres literales y excluir o recuperar por referencia explícita. Mapear las columnas anteriores sin uniones por IP/texto; mantener cuerpos vacíos y campos desconocidos. Ordenar por hora interpretada y `rev_id` como desempate; escribir el dataset y su resumen fuera de los originales.

**Depende de:** T1. **VALIDATE:** `uv run pytest -q tests/test_prepare.py` en GREEN. No introducir lógica del portero.

### T3. ADD el dataset completo y verificarlo como tabla

**Salidas:** `data/prepared/wiki/events.jsonl` y `cleaning.json`. Procesar el corpus entero y conciliar 14.591 entradas con utilizadas/excluidas, recuperaciones e IDs. Contrastar las referencias de la exploración sin forzar los conteos. Cargar solo el dataset con pandas y comprobar filas, columnas, cuerpos vacíos y referencias; no generar una segunda copia como requisito.

**Depende de:** T2. **VALIDATE:** comando de preparación anterior y `uv run pytest -q tests/test_prepare.py -k 'corpus_accounting or dataframe_contract'`.

### T4. UPDATE instrucciones y revisar la preparación

**Archivo:** `README.md`. Documentar entradas, salidas, comando y carga tabular verificadas. Revisar el código con un especialista, corregir hallazgos y repetir los comandos de aceptación. Declarar la preparación disponible solo cuando funcione; el proyecto continúa con las fases 2–5 del PRD.

**Depende de:** T3. **VALIDATE:** los tres comandos de aceptación. Cierre: dataset y limpieza reproducibles, consultables y con procedencia.

## Notes
