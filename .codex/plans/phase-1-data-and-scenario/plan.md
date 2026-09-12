# Plan: fase 1 — datos y escenario de demostración

**Status**: draft

## Goal

Preparar datos de la wiki, política y casos propios para enseñar una tarea de investigación con el portero entre llamada y ejecución. Usaremos llamadas guionizadas y herramientas locales, sin LLM ni gasto de API. Esta fase prepara las entradas y expectativas; la fase 2 implementará el portero y ejecutará la escena. Presupuesto orientativo: dos horas.

## Findings

Exploración local del 12-09-2026, leyendo los comprimidos como datos:

- `revisions.jsonl.gz`: 14.591 filas, sin `rev_id` duplicados; todas tienen hora interpretable, página y cuerpo de texto.
- Excluir las 31 revisiones de los tres nombres humanos de `labels.jsonl.gz` y las 899 sin nombre deja 13.661 revisiones de 3.099 IDs. Es la base antes de recuperaciones justificadas. Los anónimos no tienen `related_event_id`.
- Hay 74 cuerpos vacíos válidos en esa base. `request_action` contiene `form_edit` en 14.482 filas originales y carece de valor en 109; no es el nombre recuperado de una herramienta de LLM.
- La matriz ya existe en el diseño, §5. `docs/datos-replay-hf.json` contiene nueve fases, cinco días, 21 ejemplos y seis puntos acumulados.
- No hay implementación ni pruebas. `pyproject.toml` declara pandas, PyYAML y pytest. El PRD vigente está en la raíz.

## Decisions

- **Usuario, 12-09-2026 — pruebas propias.** Nada de ExploitGym entra en código, encargos o casos. Escribimos la tarea de investigación y las llamadas; ExploitGym queda como contexto documental del control existente y de la matriz. Sus encargos de explotación pertenecen a otro escenario.
- **Usuario, 12-09-2026 — demostración de sprint.** Enseñar trabajo autorizado y veto antes del efecto, con comprobaciones concretas. Se retira la exclusividad de `wiki.edit`: el entorno local necesita operaciones legítimas y el intento de edición prohibida. No convertir el caso de uso en un benchmark general.
- **Usuario, 12-09-2026 — sin gasto de modelo.** Reproducir llamadas escritas por nosotros. Portero y efectos locales reales; generación guionizada, sin atribuirla a un agente real. Conectar un LLM no hace falta para demostrar el veto.
- **Alcance heredado.** Una política, cinco operaciones autorizadas y denegación por defecto; memoria por ID. Concretar la regla y sus parámetros es una entrega de fase 1, anterior a implementar o medir. No atribuir mejora de memoria al histórico.

## Context

Leer `AGENTS.md:18` (stack), `PRD.md` §§5, 7 y 11 (datos, aceptación y fases), y `docs/proyecto-portero-tool-calls.md` §§5, 11–13 y 16–18 (matriz, procedencia, política y casos). Seguir el programa local Python/YAML/JSONL; no usar plantillas de otros proyectos.

Rutas concretas:

- **Leer:** `data/collusion-wiki/revisions.jsonl.gz`, `data/collusion-wiki/labels.jsonl.gz`; otros originales únicamente para comprobar referencias explícitas de recuperación. `docs/datos-replay-hf.json` solo alimenta la matriz.
- **Crear:** `bouncer/__init__.py`, `bouncer/prepare.py`, `tests/test_prepare.py`, `tests/test_scenario.py`, `scenarios/research.md`, `scenarios/research-cases.jsonl`, `policies/research.yaml`.
- **Generar:** `data/prepared/wiki/events.jsonl`, `data/prepared/wiki/cleaning.json`.
- **Actualizar:** `docs/proyecto-portero-tool-calls.md` §5 y `README.md` con preparación verificada. Las contradicciones de alcance de PRD, diseño y README se corrigen durante esta planificación.

Nunca modificar originales ni ejecutar contenido del corpus. Antes de cerrar afirmaciones históricas de la matriz, comprobar sus fuentes primarias; no abrir una investigación general ni visitar URLs del corpus.

## Acceptance contract

- [ ] Entrada = usadas + excluidas, sin doble conteo. Recuperaciones identificadas como subconjunto, con evidencia; cualquier diferencia respecto a la base medida queda explicada. **Comprueba:** `test_corpus_accounting` y resumen de limpieza.
- [ ] Cada evento conserva revisión/fila de origen, ID literal, hora/calidad temporal y campos observados, adaptados y desconocidos. Preserva cuerpos vacíos; no inventa identidades ni herramientas. **Comprueban:** `test_provenance_and_empty_bodies`, `test_missing_identity`, `test_missing_request_action`.
- [ ] Dos preparaciones con igual ID producen archivos idénticos; desempate estable sin atribuir orden real subsegundo. Originales con hashes intactos; sin etiquetas de página ni resúmenes futuros en eventos. **Comprueban:** `test_repeatable_preparation`, `test_originals_unchanged`, `test_event_fields`.
- [ ] Encargo propio, cinco permisos con argumentos y origen, recursos locales, política versionada y denegación por defecto. Casos de las cinco operaciones legítimas, edición prohibida y operación desconocida, con decisión y efecto esperado: lectura con contenido, respuesta entregada y wiki intacta tras bloqueo. **Comprueba:** `test_scenario_contract` y lectura conjunta de escenario, política y casos; los efectos se ejecutan en fase 2.
- [ ] Regla de memoria con condición, parámetro/unidad y consumo/liberación explícitos; secuencia legítima, límite excedido y otro ID independiente, con expectativas para capa 1 y 1+2. Repetir una espera no es indebido sin una restricción de la tarea. **Comprueba:** `test_memory_case_contract`; comprobar ejecución real corresponde a fase 2.
- [ ] Matriz de nueve fases con ambos controles, coste cualitativo, encargo supuesto, fracciones y límites; sin inventar mediciones ni precocidad. **Comprueba:** revisión de §5 contra agregados y fuentes primarias citadas.

Comandos de aceptación que existirán al implementar la fase:

```sh
uv run pytest -q tests/test_prepare.py tests/test_scenario.py
uv run python -m bouncer.prepare --output-dir data/prepared/wiki --replay-id phase1-wiki
git diff --check
```

## Out of scope

- Portero, ejecución de herramientas y comparación final: fases 2 y 3.
- LLMs, APIs, navegador, servicios o búsqueda de corpus benignos como condición para avanzar.
- Código, instancias, encargos o herramientas de ExploitGym.
- Ejecutar el corpus, reconstruir el incidente, incorporar capas opcionales o estimar tasas generales de detección.

## Interfaces

`events.jsonl`: un evento por revisión utilizada, con referencia, `agent_id` y procedencia, ID de reproducción asignado, hora/calidad, operación adaptada, destino, argumentos disponibles y desconocidos. La política procede del experimento, nunca del contenido del corpus.

`research-cases.jsonl`: ID de caso, grupo (preparación o comprobación), secuencia propia y decisión, resultado o estado local esperado para ambas configuraciones. Las expectativas no entran en los argumentos del portero. Sin formato obligatorio de un proveedor de LLM.

## Tasks

1. **CREATE escenario, política y casos.** Escribir los recorridos legítimo, edición prohibida y límite con memoria; fijar parámetros antes de medir. Crear primero comprobaciones del contrato de datos. **VALIDATE:** `uv run pytest -q tests/test_scenario.py`.
2. **CREATE preparación y pruebas.** RED y después transformación mínima, recuperación solo por referencias explícitas y exclusiones justificadas. Sin inferencia por texto/IP ni motor genérico de recuperación. **VALIDATE:** `uv run pytest -q tests/test_prepare.py`.
3. **ADD derivados y UPDATE matriz.** Conciliar datos y verificar integridad; cerrar §5 con fuentes y coste cualitativo. **VALIDATE:** comando de preparación anterior y `uv run pytest -q tests/test_prepare.py`; revisión documental de nueve filas.
4. **UPDATE instrucciones y revisar.** Documentar el comando que funciona y revisar código con especialista. Corregir hallazgos. **VALIDATE:** los tres comandos de aceptación y contrato documental completo.

## Notes
