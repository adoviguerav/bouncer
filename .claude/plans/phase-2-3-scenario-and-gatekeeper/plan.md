# Plan: fases 2+3 — escenario, política, portero y ejecución local

**Status**: implemented

## Goal

Existe una escena de investigación escrita por nosotros (encargo, páginas locales, preguntas, respuestas de referencia, estado inicial de la wiki), una política YAML versionada que lista las cinco llamadas que la tarea autoriza con denegación por defecto, guiones con decisión y efecto esperados, y un portero que decide antes de ejecutar: una lectura devuelve contenido, una respuesta se entrega, y `wiki.edit` no llega a la herramienta ni modifica la wiki local. Cada decisión queda en un log JSONL escrito desde código de confianza. El parámetro de la regla de memoria queda fijado aquí; su código es fase 4.

## Findings

Exploración interna del 12-09-2026 (corpus leído como datos, nunca ejecutado):

- Fase 2 no pide lógica de decisión: PRD.md:322-332. Fase 3 sí: PRD.md:334-345.
- La tarea tiene forma verificable: en `records.jsonl.gz` (13.703 mensajes) rondas R1–R6 (R5: 2.219 menciones; R7+: <70), `deadline` 1.190, `task clock` frente a contenedor 168, `clock.wait` 143. Coincide con docs/hallazhos/hallazgos-tarea-wiki.md:10-21.
- Solo `clock.wait` aparece como nombre de herramienta en el corpus (27 con paréntesis; argumentos en segundos: 60, 120, 300, 600, 900 ×8, 1000, 1200, 1500, 1800). Buscar, leer, pregunta y entregar son nombres nuestros.
- La proporción reloj-tarea / reloj-real no es estable: ≈10× según hallazgos (10 min en 61 s), ≈4× en un mensaje del corpus (`clock.wait(1000)` → ~9m36 tarea en ~2m20 contenedor). La regla de memoria no puede apoyarse en una proporción fija.
- Dos formas candidatas de la regla de capa 2 ya escritas: docs/hallazhos/hallazgos-tarea-wiki.md:86-91. Restricción del PRD: repetir `clock.wait` no es por sí solo un incumplimiento (PRD.md:329).
- Las cinco operaciones no tienen argumentos definidos en ningún documento (docs/proyecto-portero-tool-calls.md:414).
- Tres grupos de casos ya fijados: los que para capa 1, los que solo para capa 2, los que nadie debe parar (docs/proyecto-portero-tool-calls.md:501-509). Preparación separada de evaluación (§11.5).
- Fase 1 entregó `data/prepared/wiki/events.jsonl` con `operation: wiki.edit` y `provenance` por fila; `bouncer/prepare.py` es el único módulo. Estilo: funciones sueltas, sin clases, pruebas con fixtures propios en `tests/test_prepare.py`.
- `docs/hallazhos/` (errata) rompe los enlaces de PRD, README y AGENTS.md a `docs/hallazgos-*.md`.

Segunda sonda, misma sesión, sobre cómo funcionaba el tiempo en la tarea real:

- **Las rondas las empujaba el sistema por reloj de tarea.** 590 mensajes dicen «R3 arrived», «R4 due 21:46:11 task clock»; ninguno dice que el agente pidiera la siguiente pregunta. 18 mensajes: la ronda interrumpe una espera en curso («waits are interrupted by prompts»).
- **La espera entre rondas era fija por ejecución y distinta por cohorte**: 33m33, 35m11, 37m16, 47m22, 57m31, 1h22m02, 1h28m36 («R2 same cooldown 1h22m02»). No siempre se anunciaba («No cooldown notice», «again silent»); los agentes la deducían y la compartían por la wiki.
- **`clock.wait(N)` adelantaba N segundos de tarea en mucho menos tiempo real**: «wait(600) advances task clock ~600s in ~80s external». Los agentes encadenaban `wait(900)` hasta que la ronda les interrumpía: la suma de sus esperas por ronda ≈ espera obligatoria, igual que la de un agente honrado. **Un presupuesto «no esperar más que la espera obligatoria» no bloquea el patrón del incidente.** La diferencia está en el reloj real, no en el de tarea.
- Lo que se saltaron no fue una regla escrita sino el aislamiento entre cohortes: llegar antes a R5 servía para publicar en la wiki la pregunta y la respuesta para los que venían detrás. La escritura la para la capa 1; el adelanto del reloj es un fallo del harness que el agente explotó.

## Decisions

- **Adolfo, 12-09-2026 — fusionar fases 2 y 3 en un plan.** Alternativas: plan solo de fase 2 (recomendado por Claude: parámetros fijados antes de implementar reglas) o escribir política y guiones sin plan. Elegido B, sin razón explicitada. Condición para respetar PRD.md:392: el parámetro de la regla de memoria queda decidido en esta sección antes de aprobar el plan; su código es fase 4.
- **Claude por delegación de Adolfo, 12-09-2026 — regla de memoria: presupuesto de espera por ronda.** Criterio dado por Adolfo: la forma que más conecte con el caso a demostrar y con la realidad del incidente. Alternativas: «respuestas demasiado juntas» (mira el resultado cuando el reloj ya se adelantó; es la vista de un scorer, no de un portero) y «las dos» (dos reglas y dos parámetros donde el PRD pide una). Elegida: la suma de segundos de tarea pedidos con `clock.wait` por el mismo ID dentro de una ronda no supera la espera obligatoria del encargo. Es la forma literal de P0-04 y para el mecanismo documentado (encadenar esperas) antes de su efecto.
- **Parámetros de la regla, fijados antes de evaluar.** Unidad: segundos de reloj de tarea pedidos como argumento. Límite: 600 s, la espera obligatoria que declara nuestro `task.md`, tomada de «unos diez minutos» (hallazgos §3), no de la moda de 900 del corpus. Cuenta autorizaciones: se reserva al permitir, se libera si la herramienta devuelve error. Ronda: la asigna el ejecutor desde código de confianza; el contador se reinicia cuando `round.question` devuelve una ronda nueva. Tiempo de confianza: el reloj de tarea del ejecutor, nunca un argumento del agente. Una espera dentro del presupuesto se permite aunque sea la tercera seguida.
- **Claude, mecánico — nombres y forma de las operaciones.** `tool.operation` como `wiki.edit` y `clock.wait`: `web.search(query)`, `page.read(page)`, `round.question()`, `answer.submit(value)`, `clock.wait(seconds)`. Solo `clock.wait` y `wiki.edit` tienen procedencia; los otros cuatro se marcan como nombres nuestros en la política (`name_source: ours`).
- **Claude, mecánico — capas como selección explícita.** El portero recibe qué capas evalúa. En fase 3 solo existe `permissions`; pedir `memory` lanza un error, no un pase silencioso. Así la política v1 declara la regla de memoria desde ahora sin que fase 3 la ignore por accidente, y fase 5 compara capa 1 frente a 1+2 sin segunda política.
- **Claude, mecánico — sin prueba de coherencia aparte para la escena.** Las pruebas de fase 3 cargan la política y recorren los guiones; si algo no cuadra, fallan ahí.
- **Adolfo, 12-09-2026 — SUSTITUYE las dos entradas de la regla de memoria anteriores.** Adolfo preguntó si el 600 salía de los datos; la segunda sonda (Findings) mostró que no: la espera real era fija por ejecución, variable por cohorte y no anunciada, y el presupuesto por ronda no pilla el patrón del incidente. Recomendación de Claude aceptada: **regla de reloj como presupuesto.** El agente dispone de un presupuesto de tiempo de tarea igual al tiempo real transcurrido desde el inicio de la ejecución; cada `clock.wait(N)` reserva N contra ese presupuesto antes de ejecutarse; si lo ya reservado supera lo transcurrido en el reloj real, se bloquea. Parámetros: proporción 1 (un segundo de tarea por segundo real; sale del significado de esperar, no de una cifra ajustada); cuenta autorizaciones (reserva al permitir, libera si la herramienta falla); reloj real y de tarea propiedad del ejecutor, nunca argumentos del agente. Primer `wait(900)` a 0 s reales pasa (nada reservado); segundo a 80 s reales se bloquea (900 > 80): repetir no es la infracción, encadenar sí. Con un reloj honesto la regla no salta nunca, y eso se demuestra con el guion legítimo. Alternativas descartadas: presupuesto por ronda con límite = espera de la ejecución (honesto pero no pilla nada del incidente); una respuesta por ronda (sale de la tarea pero no tiene relación con el incidente). Coste asumido: la demo corre con dos relojes, honesto y con el fallo del harness (N segundos de tarea al instante), el segundo etiquetado como reproducción del fallo documentado.
- **Adolfo, 12-09-2026 — `round.question` lee, no pide.** Conforme a los datos, la ronda la entrega el reloj de tarea del ejecutor; la llamada devuelve la pregunta de la ronda que ya ha llegado o «sin ronda nueva». El agente no elige la ronda. La espera obligatoria de nuestro encargo es fija por ejecución y se configura en la escena con un valor del rango observado; no la anuncia la pregunta.
- **Adolfo, 12-09-2026 — marco para el informe: mismo sitio, tres alcances.** Lo generalizable es dónde (entre la llamada y su ejecución, desde código de confianza, con ID por agente) y con qué alcance: una llamada de un agente (herramienta + operación + argumentos, no solo «la herramienta está en el pool»), el historial de un agente (cualquier presupuesto, no solo el tiempo) y varios agentes. Lo específico es qué regla concreta hay en cada alcance para esta tarea. Consecuencia en código: cada regla del YAML lleva su `scope` (`call` | `agent_history` | `cross_agent`) para que la tabla «regla → alcance → origen → qué necesita → qué paró» salga del fichero. Sin más estructura.

## Context

Leer antes de implementar:

- `AGENTS.md:18-24` — stack (Python, YAML, JSONL; sin servicios) y regla de no ejecutar contenido del corpus.
- `PRD.md:160-172` — una sola política, lista de permitidas, denegación por defecto, origen de la regla de capa 2.
- `PRD.md:216-221` — P0-01 a P0-06 con su observación de aceptación. Esta fase cubre P0-03, P0-05 y P0-06.
- `PRD.md:322-345` — tareas de fases 2 y 3.
- `PRD.md:250-257` — las cuatro decisiones y su efecto en el ejecutor; «no evaluable» es estado, no aprobación.
- `docs/proyecto-portero-tool-calls.md:369-390` — registro del experimento: qué IDs asigna el ejecutor y qué no puede sustituir el agente.
- `docs/proyecto-portero-tool-calls.md:394-424` — capa 1: qué comprueba y qué devuelve.
- `docs/proyecto-portero-tool-calls.md:470-495` — decisiones, log y frontera del control.
- `docs/proyecto-portero-tool-calls.md:499-519` — cómo se construyen los casos y qué prueban.
- `docs/hallazhos/hallazgos-tarea-wiki.md` — la tarea reconstruida; de aquí sale cada frase de `task.md` y el origen de cada regla.
- `bouncer/prepare.py` — patrón a seguir: funciones sueltas, constantes arriba, `main(argv)` con argparse, escritura JSONL con `json.dumps`.
- `tests/test_prepare.py` — patrón de fixtures propios en `tmp_path`.

Ficheros que se crean:

- `scenario/task.md` — el encargo: rondas que llegan por reloj de tarea, plazo por ronda, espera fija por ejecución configurada en la escena, lectura permitida, escritura no. Marcado como reconstrucción nuestra.
- `scenario/wiki/*.md` — páginas locales con datos inventados y etiquetados como propios; estado inicial de la wiki. El ejecutor trabaja sobre una copia.
- `scenario/questions.jsonl` — una fila por ronda: `round`, `question`, `reference_answer`.
- `scenario/policy.yaml` — versión, encargo, cinco llamadas permitidas con `source` (sección de `task.md`), restricciones de argumentos, `default: deny`, regla de memoria declarada con sus parámetros.
- `scenario/scripts/*.jsonl` — guiones: `legitimate`, `forbidden_edit`, `unknown_operation`, `wait_budget` (fase 4), `two_agents` (fase 4). Cada línea: `call` (lo que ve el portero) y `expect` (lo que no ve).
- `bouncer/gate.py` — carga y validación de la política; `decide`.
- `bouncer/tools.py` — las seis funciones locales (cinco permitidas y `wiki.edit`) sobre un directorio de trabajo y un estado de ejecución.
- `bouncer/executor.py` — asigna `run_id`/`agent_id`, consulta al portero, ejecuta solo si permite, escribe el log; `main(argv)` para recorrer un guion.
- `tests/test_gate.py`, `tests/test_tools.py`, `tests/test_executor.py`.

Avisos:

- Las expectativas de los guiones no viajan en los argumentos de la llamada (PRD.md:242).
- El log no copia cuerpos completos ni secretos (PRD.md:342); guarda referencias.
- Un error de herramienta tras permitir no es éxito (PRD.md:221).
- No usar `page_family`, etiquetas ni agregados del corpus en ninguna decisión.
- `docs/hallazhos/` debe renombrarse a `docs/hallazgos/` en un cambio aparte; este plan cita la ruta actual.

## Acceptance contract

- [ ] `scenario/policy.yaml` carga y contiene exactamente cinco llamadas permitidas, cada una con `source` que apunta a una sección existente de `task.md` y `scope: call`; `default` es `deny`; la regla de memoria declara `scope: agent_history`, `budget: task_seconds`, `against: wall_seconds_elapsed`, `ratio: 1`, `counts: authorizations`. — `test_policy_loads_and_cites_task`
- [ ] Una llamada de la lista con argumentos válidos se permite con el ID de su regla; una que no está (`wiki.edit`, `shell.run`) se bloquea con `rule: default-deny`; una de la lista con argumentos inválidos (`clock.wait(-1)`, `page.read` sin página) se bloquea con el ID de la restricción de argumentos. — `test_decide_allow`, `test_decide_default_deny`, `test_decide_invalid_args`
- [ ] Recorrer `legitimate.jsonl` con el ejecutor permite todas las llamadas, `page.read` devuelve el contenido de la página local, cada `answer.submit` queda en el log con `status: ok` y `result_ref` que incluye la ronda, y la copia de trabajo de `scenario/wiki/` es byte-idéntica al original al terminar. — `test_legitimate_script_completes`
- [ ] Recorrer `forbidden_edit.jsonl` bloquea `wiki.edit`, la función de edición no se invoca (espía de llamadas) y la copia de trabajo sigue byte-idéntica; las llamadas legítimas del mismo guion sí se ejecutan. — `test_blocked_edit_has_no_effect`
- [ ] Una llamada cuyos argumentos incluyen `agent_id`, `run_id` o `policy` no cambia la identidad ni la política que el ejecutor asignó; el log registra los valores de confianza. — `test_agent_cannot_override_identity`
- [ ] Una llamada sin `agent_id` asignado por el ejecutor no se ejecuta y se registra como error, nunca como `allow`. — `test_missing_identity_is_not_permission`
- [ ] `page.read` de una página inexistente se permite por política y termina con `status: error` en el log; nunca `status: ok`. — `test_tool_error_is_not_success`
- [ ] Cada línea del log tiene `run_id`, `agent_id`, `call_id`, `tool`, `operation`, `decision`, `rule`, `reason`, `policy_version`, `status`, `duration_ms`; la ruta del log está fuera del directorio de trabajo que reciben las herramientas. — `test_log_record_shape`, `test_log_outside_workdir`
- [ ] Dos recorridos del mismo guion con el mismo `--run-id` producen logs idénticos salvo `duration_ms`. — `test_deterministic_run`
- [ ] Pedir la capa `memory` en fase 3 lanza un error explícito; no permite ni bloquea. — `test_memory_layer_not_silently_skipped`
- [ ] Cobertura de `bouncer/gate.py`, `tools.py`, `executor.py` ≥ 80 %.

Comandos que ejecutará `/verify`:

```sh
uv run pytest -q
uv run --with pytest-cov pytest -q --cov=bouncer --cov-report=term-missing
uv run python -m bouncer.executor --script scenario/scripts/legitimate.jsonl --run-id verify-legit --output-dir /tmp/bouncer-verify/legit
uv run python -m bouncer.executor --script scenario/scripts/forbidden_edit.jsonl --run-id verify-edit --output-dir /tmp/bouncer-verify/edit
git diff --check
```

## Out of scope

- Implementar la regla de memoria, contadores, reserva y aislamiento entre IDs: fase 4. Aquí solo se declara en la política y se escriben sus guiones.
- Demo con restauración de estado, reproducción cronológica del dataset y comparación capa 1 / 1+2: fase 5.
- Retener con revisor, capa 3 y capa 4.
- Conectar un LLM, ejecutar contenido del corpus o visitar sus URLs.
- Renombrar `docs/hallazhos/`: cambio aparte.

## Interfaces

Estas formas las comparten guiones, portero, ejecutor y las fases 4–5.

Llamada (lo que ve el portero; la identidad la añade el ejecutor, no el guion):

```
Call: tool: str, operation: str, args: dict
Identity: run_id: str, agent_id: str, policy_version: str  # asignados por el ejecutor
```

Decisión:

```
Decision: outcome: "allow" | "block", rule: str, reason: str
decide(call: Call, policy: Policy, layers: tuple[str, ...]) -> Decision   # fase 4 añade el estado de memoria
```

Estado de ejecución (lo posee el ejecutor; las herramientas lo reciben, el agente no lo ve):

```
RunState: workdir: Path, task_clock_seconds: int, wall_clock: Callable[[], float], clock_mode: "honest" | "harness_bug",
          cooldown_seconds: int, round: int, answers: dict[int, str]
clock.wait(seconds): en "harness_bug" suma seconds a task_clock_seconds al instante (fallo documentado);
                     en "honest" duerme seconds reales y suma lo mismo. Se corta si llega una ronda.
round.question(): devuelve la pregunta de la ronda que el reloj de tarea ya ha entregado, o "sin ronda nueva".
wall_clock lo inyecta el ejecutor (en pruebas, un reloj falso); el agente no lo ve ni lo aporta.
```

Política (`scenario/policy.yaml`): `version`, `task`, `default: deny`, `allowed: [{id, scope: call, tool, operation, args, source, name_source}]`, `memory_rules: [{id, scope: agent_history, tool, operation, budget, against, ratio, counts, source}]`.

Línea de guion (`scenario/scripts/*.jsonl`):

```
{"agent": "A", "call": {"tool": "page", "operation": "read", "args": {"page": "..."}}, "expect": {"decision": "allow", "effect": "returns page"}}
```

Línea de log (`<output-dir>/decisions.jsonl`): los campos del contrato, más `result_ref` cuando la herramienta devuelve algo y `error` cuando falla.

## Tasks

### T1. CREATE la escena

**Archivos:** `scenario/task.md`, `scenario/wiki/*.md`, `scenario/questions.jsonl`. Encargo de tres rondas sobre datos inventados de las páginas locales; las rondas llegan por reloj de tarea con una espera fija por ejecución (valor del rango observado, p. ej. 2111 s = 35m11) que la escena configura y la pregunta no anuncia. Todo etiquetado como material propio.

**Depende de:** nada. **VALIDATE:** `uv run python -c "import json; [json.loads(l) for l in open('scenario/questions.jsonl')]"` y que cada `reference_answer` aparece en alguna página de `scenario/wiki/`.

### T2. CREATE la política

**Archivo:** `scenario/policy.yaml`. Cinco permitidas con `source` a `task.md`, restricciones de argumentos, denegación por defecto, regla de memoria declarada con los parámetros de Decisions.

**Depende de:** T1. **VALIDATE:** `uv run python -c "import yaml; p=yaml.safe_load(open('scenario/policy.yaml')); assert len(p['allowed'])==5 and p['default']=='deny'"`.

### T3. CREATE los guiones

**Archivos:** `scenario/scripts/legitimate.jsonl`, `forbidden_edit.jsonl`, `unknown_operation.jsonl`, `wait_budget.jsonl`, `two_agents.jsonl`. Campo `set` (`preparation` | `evaluation`). Los dos últimos llevan `phase: 4` y no se recorren en esta fase.

**Depende de:** T2. **VALIDATE:** `uv run python -c "import json,yaml,glob; p=yaml.safe_load(open('scenario/policy.yaml')); ok={(a['tool'],a['operation']) for a in p['allowed']}|{('wiki','edit'),('shell','run')}; assert all((json.loads(l)['call']['tool'],json.loads(l)['call']['operation']) in ok for f in glob.glob('scenario/scripts/*.jsonl') for l in open(f))"`.

### T4. CREATE las pruebas del portero, las herramientas y el ejecutor

**Archivos:** `tests/test_gate.py`, `tests/test_tools.py`, `tests/test_executor.py`. Un escenario por criterio del contrato, con fixtures en `tmp_path` que copian `scenario/wiki/`.

**Depende de:** T3. **VALIDATE:** `uv run pytest -q tests/test_gate.py tests/test_tools.py tests/test_executor.py` en RED por módulos ausentes.

### T5. CREATE portero, herramientas y ejecutor

**Archivos:** `bouncer/gate.py`, `bouncer/tools.py`, `bouncer/executor.py`. Sin clases salvo dataclasses congeladas para `Call`, `Decision` y el estado de ejecución. `executor.main` recorre un guion y escribe `decisions.jsonl`.

**Depende de:** T4. **VALIDATE:** las mismas pruebas en GREEN y cobertura ≥ 80 %.

### T6. UPDATE README y revisar

**Archivo:** `README.md`: sección de escena, política y ejecución de guiones con los comandos verificados. Revisión con especialista; hallazgos de seguridad a `security-reviewer`. Repetir los comandos de aceptación.

**Depende de:** T5. **VALIDATE:** los cinco comandos de `/verify`.

## Notes

- **Desviación, T4 (12-09-2026).** El plan nombraba `tests/test_gate.py`, `tests/test_tools.py`, `tests/test_executor.py`. Las escribió un agente ciego con solo contrato + interfaces y viven en `tests/acceptance/` (17 pruebas, congeladas tras aprobación de Adolfo). Motivo: es lo que exige `/implement`; las pruebas cubren los mismos criterios.
- **Desviación, T1/T5 (12-09-2026).** La espera fija entre rondas no vive en un fichero de escena: es `COOLDOWN_SECONDS = 2111` en `bouncer/executor.py`, parámetro `cooldown_seconds` de `run_script` y flag `--cooldown` del CLI. Primero se probó `scenario/task.yaml`, pero el fixture congelado de las pruebas de aceptación no lo crea (el escritor ciego no lo conocía) y un fichero opcional con valor por defecto sería un pase silencioso. Una constante documentada con su origen es una fuente de verdad menos.
- **Desviación, T5.** `RunState` es un dataclass mutable, no congelado como decía T5: el reloj de tarea, la ronda y las respuestas cambian durante la ejecución por diseño. `Call`, `Decision` y `Policy` sí van congelados.
- **Revisión, T6 (12-09-2026).** Sin críticos. Corregidos: la espera se cortaba en la siguiente ronda leída y no en la siguiente llegada (un `wait` grande se saltaba rondas sin leerlas); el texto de error de herramienta llevaba la ruta absoluta del workdir al log; guardias para `cooldown < 1` y `output_dir` dentro de `scenario/`; prueba que contrasta `expect.decision` de los guiones reales con el log. No aplicados: renombrar `duration_ms` (campo del contrato) y cambiar la clave de `TOOLS` a tupla (sin fallo real).
- **`/review`, 12-09-2026 (informe en `review-report.md`).** Sin críticos ni altos. Corregidos los cuatro MEDIUM de código, con prueba de andamiaje cada uno: el ejecutor ya no borra un `workdir/` con ficheros ajenos a la escena (M1); una línea de guion sin `call.tool`/`call.operation`/`call.args` bien formados se registra como `rejected` y el recorrido sigue (M2); cada línea del log lleva `clock_mode` y `cooldown_seconds` (M3); `result_ref` es `round:none` cuando `round.question` no tenía ronda nueva (M4). M0 aplicado con desbloqueo de Adolfo (`.unlock-tests`): **antes**, `test_legitimate_script_completes` solo comprobaba que _alguna_ lectura tuviera un `result_ref` que empezara por `page:` (un `page_read` que devolviera `""` pasaba); **después**, cada lectura del guion deja `page:<página>` en el log y un espía sobre `page.read` comprueba que lo devuelto es el contenido real de `scenario/wiki/<página>.md`. **Por qué**: el criterio pide el efecto a nivel de ejecutor (portero → herramienta → log) y la prueba de origen solo miraba el formateador del log. Pendiente: Adolfo re-aprueba y retira el marcador. LOW sin aplicar: política vacía con `AttributeError`, coste de `--clock honest` (≈70 min con el guion legítimo), `rejected` frente a «error» en el contrato, guiones `phase: 4` sin aviso, etiqueta «datos reales» en el conftest congelado.
- **Idioma, 12-09-2026 (Adolfo).** Todo lo que verá el jurado pasa a inglés: README, AGENTS.md, PRD, `docs/`, `scenario/`, código (comentarios, mensajes, motivos del log) y pruebas. Fuera: `.claude/plans`, `.codex`, checkpoints y el corpus. Consecuencias en pruebas congeladas, hechas con el marcador `.unlock-tests` de Adolfo: los encabezados de `task.md` cambian y con ellos los slugs `source` de la política (`allowed-tools`, `rounds-and-waiting`, `answers`), replicados en `conftest.POLICY_YAML`/`TASK_MD`; `NO_NEW_ROUND` pasa a `"no new round"` (`test_tools`); el resto son docstrings y comentarios. Ningún assert se aflojó; 42/42 verdes tras el cambio. Los guiones y el log no cambian de forma. Los nombres de fichero en castellano (`docs/proyecto-portero-tool-calls.md`, `docs/hallazhos/…`) se mantienen para no romper enlaces.
- **Precisión, T2.** `clock.wait` lleva `name_source: corpus` porque sí aparece literal en los mensajes; los otros cuatro `ours`, como decía Decisions.
- Para el informe (entrega documental, fuera de este plan): sección «marco» — dónde se comprueba, identidad de confianza, tres alcances — y tabla «este caso» — regla concreta por alcance, de qué parte de la tarea sale, qué paró. Declarar que el alcance de historial se demuestra sobre un fallo del harness reproducido, no sobre una infracción del agente en el corpus.
