# Review: fases 2+3 — escenario, política, portero y ejecución local

**Fecha:** 12-09-2026 · **Revisor:** un `code-reviewer` ciego (plan sin Notes + diff + CLAUDE.md) · **Filtro adversarial:** Claude, en sesión · **Árbol tras la revisión:** intacto (mismos 21 ficheros, 1.197/4 líneas; el revisor trabajó sobre una copia en el scratchpad).

## Resumen

Sólido. La denegación por defecto, la validación de argumentos, el veto antes de invocar la herramienta, la identidad desde código de confianza y el log fuera del directorio de trabajo funcionan y están probados; ningún agujero explotable desde los guiones. Lo primero que arreglar: el ejecutor borra sin aviso cualquier `workdir/` que ya exista bajo `--output-dir` (M1). Antes de la fase 5: el log no dice con qué reloj ni con qué espera se hizo el recorrido (M3), y la prueba de aceptación del guion legítimo no comprueba el contenido que devuelve `page.read` (M0, requiere desbloquear pruebas).

Recuento: CRITICAL 0 · HIGH 0 · MEDIUM 5 · LOW 5 · descartados o explicados por `## Notes` 5.

## Hallazgos

### MEDIUM

**M0. `tests/acceptance/test_executor.py:48-52` — la prueba del guion legítimo no comprueba el contenido devuelto por `page.read`.**
El criterio dice «`page.read` devuelve el contenido de la página local»; la prueba solo mira que _alguna_ lectura tenga un `result_ref` que empiece por `page:`, que es una propiedad del formateador del log, no de la herramienta.
Repro (revisor, sobre copia): `page_read` devolviendo `""` → `pytest tests/acceptance/test_executor.py` sigue en `8 passed`. La suite completa sí cae, pero en `test_tools.py::test_page_read_returns_local_page`, que no ejerce la cadena portero → herramienta → log.
Refutación: `test_tools.py` cubre el efecto aislado; por eso el daño práctico es pequeño. Sobrevive porque el criterio pide el efecto a nivel de ejecutor y la aserción es `any`, no `all`.
Severidad: el revisor la marcó CRITICAL aplicando la regla «prueba debilitada». No aplica: la prueba no se editó ni se aflojó, la escribió así el agente ciego y Adolfo la aprobó. Es una prueba débil de origen, no una manipulación. Queda **MEDIUM · CONFIRMED**. Arreglarla exige abrir `tests/acceptance/` (marcador `.unlock-tests`, decisión de Adolfo): comparar el `result_ref` de _cada_ lectura con la página del guion y contrastar el contenido leído con el fichero de `workdir`.

**M1. `bouncer/executor.py:88-91` — `shutil.rmtree` borra cualquier `workdir/` preexistente bajo `--output-dir`.**
Repro (revisor): `victim/workdir/mis-notas.md` y `victim/workdir/subdir/b.txt`; `--output-dir victim` → solo quedan las tres páginas del escenario.
Refutación: la guarda de «`output_dir` dentro del escenario» protege los originales, no el directorio del usuario; la CLI hace `mkdir(exist_ok=True)`, así que reutilizar un directorio es el camino previsto. **CONFIRMED**. Arreglo mínimo: negarse si `workdir` existe, o borrar solo los ficheros que copió el propio ejecutor.

**M2. `bouncer/executor.py:38-39` — una línea de guion malformada aborta el recorrido a mitad, sin rastro en el log.**
Repro (revisor): guion de tres líneas con la segunda sin `call` → `KeyError: 'call'`, salida 1, `decisions.jsonl` con una sola línea; la tercera ni se evalúa. Igual con `"args": "hola"`.
Refutación: el guion lo escribimos nosotros, no el agente. Sobrevive porque las reglas del proyecto piden validar en el límite y ya existe el camino correcto (`rejected` cuando falta `agent`) que aquí no se usa. **CONFIRMED**. Arreglo: validar `call`, `tool`, `operation`, `args` con el mismo trato que la falta de `agent`.

**M3. `bouncer/executor.py:41-54` — el log no registra `clock_mode` ni `cooldown_seconds`.**
Repro (revisor): recorridos con `--cooldown 2111` y `--cooldown 10`, o con `--clock honest` y `harness_bug`, producen líneas indistinguibles en esos campos porque no existen.
Refutación: el contrato no los exige. Sobrevive porque la decisión de diseño dice que el reloj con el fallo del harness va «etiquetado como reproducción del fallo documentado», y la etiqueta no está en el artefacto de evidencia; además dos recorridos con el mismo `--run-id` y distinto `--cooldown` dan logs distintos sin que nada lo explique. **CONFIRMED**. Arreglo: campos en cada línea o un `run.json` con los parámetros del recorrido.

**M4. `bouncer/executor.py:27-28` — `result_ref` de `round.question` no distingue «entregó pregunta» de «sin ronda nueva».**
Repro (Claude): dos `round.question` seguidas a reloj 0 → `m4:1 round:1` y `m4:2 round:1`; la segunda devolvió `"sin ronda nueva"`.
Refutación: no lo alcanzan los tres guiones de esta fase. Sobrevive porque `wait_budget.jsonl` (fase 4) espera justo ese caso en su última línea y el log no lo podrá demostrar. **CONFIRMED**. Arreglo: `round:none` cuando el valor es `NO_NEW_ROUND`.

### LOW

**L1. `bouncer/gate.py:43` — política vacía o malformada revienta con `AttributeError` opaco.** Repro (Claude): fichero vacío → `AttributeError: 'NoneType' object has no attribute 'get'`. Los demás errores llevan ruta y motivo. **CONFIRMED**. Una línea: `if not isinstance(raw, dict): raise ValueError(...)`.

**L2. `bouncer/tools.py:67` + README — `--clock honest` sobre `legitimate.jsonl` duerme ≈70 min.** Dos `clock.wait(2111)` reales. La única prueba del modo honesto parchea `time.sleep`; nadie lo ha ejecutado. Es el coste asumido en Decisions, pero el README anuncia el mando sin decirlo y la fase 5 necesita la comparación. **CONFIRMED** (aritmética); aviso para fase 5, no defecto.

**L3. Estado `rejected` frente al contrato.** El criterio dice «se registra como error»; el código introduce `rejected` y la prueba aprobada lo consagra (`assert line["status"] == "rejected"`). Mejor distinguirlo del error de herramienta; lo que está desfasado es la redacción del contrato. **CONFIRMED**, sin cambio de código.

**L4. Los guiones con `phase: 4` se recorren sin aviso.** `--script wait_budget.jsonl` → `5 ok, 0 blocked`, contradiciendo sus `expect`. Sin capa `memory` es el resultado correcto, pero es una trampa para quien redacte resultados. **CONFIRMED**. Sugerencia: avisar o rechazar si `phase` supera las capas activas.

**L5. `tests/acceptance/conftest.py:17,15` — «Datos reales de muestra» y `AGENT = "OpenAIHelperMay15"`.** El comentario contradice la disciplina de material propio y el nombre parece una etiqueta del corpus. No se lee ni ejecuta nada de `data/`. **CONFIRMED**, redacción; fichero congelado.

### Descartados o explicados por `## Notes` (el revisor no las vio)

- Espera fija en `COOLDOWN_SECONDS` dentro de `executor.py` y no en la escena: desviación T1/T5 registrada (el fixture congelado no crea `task.yaml`).
- `RunState` mutable: desviación T5 registrada (estado diseñado para cambiar).
- Pruebas en `tests/acceptance/` y `tests/unit/` con `tests/test_prepare.py` en la raíz: desviación T4 registrada. Queda la estructura mixta como observación.
- `wall_clock.advance` sin uso: fixture congelado que la fase 4 necesitará. Sin acción.
- `Policy` congelada con tuplas de dicts mutables: sin repro. Descartado.

## Adherencia al plan

| Ítem                                     | Estado              | Nota                                                                                                                             |
| ---------------------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| T1 escena                                | cumple              | `questions.jsonl` carga; las tres `reference_answer` aparecen en `scenario/wiki/`. Espera fija en código: desviación registrada. |
| T2 política                              | cumple              | 5 permitidas, `default: deny`, cada `source` apunta a un encabezado de `task.md`, regla de memoria con sus cinco parámetros.     |
| T3 guiones                               | cumple              | 5 ficheros, campo `set`, `phase: 4` en dos; ninguna llamada fuera de permitidas ∪ {`wiki.edit`, `shell.run`}. Ver L4.            |
| T4 pruebas                               | cumple con reserva  | Ruta distinta a la del plan (registrada). RED previo no observable desde el diff. Debilidad M0.                                  |
| T5 código                                | cumple con reserva  | Estilo de `prepare.py` respetado. `RunState` mutable (registrado).                                                               |
| T6 README + revisión                     | cumple              | Cifras del README reproducidas por el revisor (12 `ok`; 3 `ok` + 1 `blocked`).                                                   |
| AC política carga y cita `task.md`       | cumple              | Ejecutado.                                                                                                                       |
| AC allow / default-deny / args inválidos | cumple              | `clock.wait(-1)` y `page.read` sin página bloquean con `…:args`.                                                                 |
| AC guion legítimo                        | cumple en ejecución | 12/12 `ok`, `workdir` byte-idéntico. La prueba no comprueba el contenido devuelto (M0).                                          |
| AC edición prohibida sin efecto          | cumple              | Espía sin llamadas, `default-deny`, copia byte-idéntica, resto `ok`.                                                             |
| AC identidad no sustituible              | cumple              | `agent_id`/`run_id`/`policy` en args caen como «argumentos no previstos».                                                        |
| AC sin identidad no es permiso           | cumple con matiz    | `status: rejected`, `decision: null`, herramienta no invocada. Contrato decía «error» (L3).                                      |
| AC error de herramienta ≠ éxito          | cumple              | `status: error`, ruta del host sustituida por `<workdir>`.                                                                       |
| AC forma del log / fuera de workdir      | cumple              | Los 11 campos en todas las líneas. Faltan parámetros del recorrido (M3).                                                         |
| AC determinismo                          | cumple              | Frágil ante `--cooldown`/`--clock` no registrados (M3).                                                                          |
| AC capa `memory` no silenciosa           | cumple              | `NotImplementedError` en `decide` y en `run_script`, antes de escribir.                                                          |
| AC cobertura ≥ 80 %                      | cumple              | `gate.py` 100 %, `tools.py` 100 %, `executor.py` 97 %.                                                                           |
| Out of scope respetado                   | cumple              | Sin contadores ni reserva; sin demo; sin LLM; sin acceso a `data/`; `docs/hallazhos/` sin renombrar.                             |
| Añadidos no pedidos                      | menor               | `tests/unit/test_scaffolding.py`, estado `rejected`, `--cooldown`, guarda de `output_dir`. Justificables.                        |

## Lo que el diff solo no puede responder

- Si T4 estuvo en RED antes de T5: no es observable en el diff ni en el árbol.
- Comportamiento real de `--clock honest`: las pruebas parchean `time.sleep`.
- Fase 4 con `two_agents.jsonl`: hoy los dos agentes comparten un único `RunState` (ronda, reloj de tarea, `answers`). El aislamiento por ID de P0-04 obligará a separar esa parte; conviene saberlo al planificar.
- Si 2111 s y el resto de la escena resisten la reproducción histórica de la fase 5.
- Las cifras de `Findings` sobre el corpus se tomaron como dadas; nadie leyó `data/` en esta revisión.
