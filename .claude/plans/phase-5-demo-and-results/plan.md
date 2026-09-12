# Plan: fase 5 — demo, reproducción histórica y resultados

**Status**: implemented

## Goal

Un comando recorre los cinco guiones propios por el portero y enseña llamada, decisión,
regla y efecto —o ausencia de efecto—; otro recorre las 13.661 filas del corpus sin
ejecutar nada de su contenido. Los dos usan el mismo núcleo de decisión. De ahí sale
`docs/results.md`: una tabla con cantidades y denominadores que separa el registro
histórico de nuestros casos con autorización conocida, y que dice con su número lo que
cuesta la regla de memoria. Quedan cubiertos P0-07, P0-08 y la reproducción técnica de
P0-09.

## Findings

Sonda del 12-09-2026 sobre el corpus entero con la política v1 y el `decide` real
(`uv run python -` contra `data/prepared/wiki/events.jsonl`, 13.661 filas):

| capas                | decisiones      | regla                 | eventos que mira la memoria | tiempo                     |
| -------------------- | --------------- | --------------------- | --------------------------- | -------------------------- |
| `permissions`        | 13.661 bloqueos | `default-deny` ×13661 | 0                           | 18 ms (1,3 µs por llamada) |
| `permissions,memory` | 13.661 bloqueos | `default-deny` ×13661 | 0                           | 20 ms (1,4 µs por llamada) |

- **La comparación de P0-08 sobre el corpus ya está respondida y da cero diferencia.** No
  por casualidad: `bouncer/gate.py:130` empareja las reglas de memoria por `tool`/`operation`,
  `clock-budget` gobierna `clock.wait` y todas las filas del corpus son `wiki.edit`. Cero
  eventos llegan siquiera a ser mirados por la capa 2. Es el resultado que `PRD.md:223`
  exige publicar tal cual. **Consecuencia para el plan:** el contenido real de la tabla
  capa 1 vs 1+2 son los guiones propios, no el corpus.
- **La restauración de estado ya está hecha.** `bouncer/executor.py:129-136` borra y vuelve
  a copiar `scenario/wiki/` en `workdir/` en cada ejecución, y se niega si hay ficheros
  ajenos al escenario. La tarea 1 de la fase 5 no necesita código nuevo.
- **`--layers` ya existe** (`bouncer/executor.py:172`): la fase 4 construyó el interruptor
  que P0-08 necesita, sin segunda política.
- **El determinismo ya es estructural.** El reloj real por defecto empieza en cero y solo
  lo mueven las esperas honestas; `duration_ms` es el único valor de reloj real y P0-07 lo
  excluye.
- **`events.jsonl` ya está en orden cronológico** (verificado: `times == sorted(times)`).
  El recorrido es leer el fichero en orden: ni `sort` ni pandas.
- **No hay nada que reutilizar para un recorrido que no ejecute.** `decide` es pura y toma
  un `Call`, pero su único llamador es el ejecutor, y el ejecutor siempre sigue hasta
  invocar la herramienta.
- **Las 13.661 filas tienen evidencia para la comprobación.** `request_action` vale
  `form_edit` en 13.587 y `null` en 74, y la comprobación de permisos no lo lee nunca: esas
  74 son igualmente evaluables. Lo no evaluable en el registro histórico es una **regla**,
  no un evento: `clock-budget`, porque el corpus no tiene llamadas `clock.wait` ni tiempos
  de respuesta.
- 3.099 `agent_id` distintos. `time_grade`: 13.587 `reqlog`, 68 `rclog`, 6 `write_date`.

Segunda sonda, `legitimate.jsonl` (12 llamadas) por los cuatro cruces de reloj y capas:

| reloj         | capas                | ok  | bloqueadas | rondas respondidas |
| ------------- | -------------------- | --- | ---------- | ------------------ |
| `honest`      | `permissions`        | 12  | 0          | 3 de 3             |
| `honest`      | `permissions,memory` | 12  | 0          | 3 de 3             |
| `harness_bug` | `permissions`        | 12  | 0          | 3 de 3             |
| `harness_bug` | `permissions,memory` | 11  | **1**      | **2 de 3**         |

- **Una llamada bloqueada, no dos** (lo escribí a ojo antes de medirlo): cae la línea 9,
  `clock.wait`, con la razón `ResearchAgentA has 2111 task seconds reserved against 0 wall
seconds elapsed`. La línea 5 pasa siempre, porque es la primera espera.
- **Y el coste real no es esa llamada.** Sin esa espera el reloj de tarea se queda en 2111,
  la ronda 3 no llega nunca (`round.question` devuelve `round:none`) y la última
  `answer.submit` —permitida, porque la política no tiene nada que objetarle— **machaca la
  respuesta de la ronda 2 con la de la ronda 3**. El agente honrado termina con 2 de 3
  rondas y una de ellas equivocada. **Consecuencia para la tabla:** contar solo llamadas
  bloqueadas subestima lo que cuesta la regla; la tabla necesita también rondas
  respondidas.

## Decisions

- **Adolfo, 12-09-2026 — dos módulos nuevos: `replay.py` y `demo.py`.** Alternativas:
  solo `replay.py` dejando la demo como la lista de comandos del README y la tabla montada
  a mano; un único módulo con subcomandos; o un `--events` dentro del ejecutor.
  **Razón:** `replay.py` no importa las herramientas, así que «el contenido del corpus no
  se ejecuta» pasa a ser un hecho estructural en vez de un flag que se puede equivocar; y
  `demo.py` le da al jurado un solo punto de entrada. Coste: dos ficheros en vez de uno.

- **Adolfo, 12-09-2026 — al repositorio van los resúmenes y la tabla, no los registros
  completos.** Los registros por evento (13.661 líneas × 2 recorridos, ~7 MB de líneas casi
  idénticas) van a `results/`, ignorada por git, y se regeneran en 20 ms con un comando.
  Se versionan `docs/results.md` y `docs/results-summary.json`. Alternativas: commitear
  todo, commitearlo comprimido, o no commitear nada. **Razón:** P0-09 pide que los
  resultados se entreguen; quien no pueda correr `uv` tiene que ver los números, y la
  historia de git no tiene por qué cargar con 13.661 copias del mismo bloqueo.

- **Adolfo, 12-09-2026 — la ejecución bloqueada del guion legítimo sale en la tabla, con
  su etiqueta.** Cuatro filas para `legitimate.jsonl`: los dos relojes × las dos capas. La
  fila de `harness_bug` + memoria (11 `ok`, 1 bloqueada, 2 de 3 rondas) se publica
  etiquetada por lo que es: **donde el reloj de tarea corre por delante del real,
  `clock-budget` no distingue al que espera de buena fe del que hace trampa.**
  Alternativas: enseñar solo el reloj honesto
  y dejar el resto en prosa, o mandarlo a un apéndice. **Razón:** convierte el coste de la
  regla en un número medido en vez de un párrafo, y §9 pide «acciones legítimas
  bloqueadas» como métrica. **Esto no reabre la decisión del reloj simulado de la fase 4**,
  que se queda: la fila se etiqueta como límite de la regla, nunca como tasa de falsos
  positivos del método.

- **Claude, mecánico — el registro del recorrido no lleva duración por evento.** Así dos
  recorridos con las mismas entradas y capas son byte a byte idénticos y P0-07 se comprueba
  con una comparación de ficheros, sin listas de campos a excluir. El tiempo de
  comprobación (total y media por llamada, que es lo que pide §9) va en el resumen, que
  queda fuera de esa comparación.

- **Claude, mecánico — «no evaluable» se declara por regla en el resumen, no por evento.**
  El estado pertenece a la regla y la razón es la misma para las 13.661 filas; repetirla en
  cada línea son 13.661 copias de la misma frase. El resumen lleva
  `non_evaluable_rules: [{rule, reason}]`. Cada evento sí lleva su decisión real, que es lo
  que pide P0-06.

- **Claude, mecánico — en el recorrido histórico un bloqueo no actualiza estado de memoria.**
  Es la misma regla que ya aplica el ejecutor (`counts: authorizations`: se reserva después
  de permitir), no una invención para el corpus. Se declara por escrito en el resumen,
  porque `PRD.md:231` lo exige explícitamente.

- **Claude, mecánico — la llamada adaptada lleva `page` y `body`; el registro no lleva el
  cuerpo.** El evento observado es una edición con cuerpo, así que el `Call` se construye
  como `wiki.edit(page=page_key, body=body)`. Ninguna regla lo lee —`default-deny` salta
  antes de mirar argumentos— y al registro solo van `rev_id`, `source_ref`, `agent_id` y
  `page_key`. Nada de ese contenido se ejecuta ni se visita.

- **Claude, mecánico — el recorrido lee el fichero línea a línea, sin pandas.** Ya está
  ordenado y no hay nada que agregar durante el recorrido. pandas se queda donde hace
  falta, en `prepare.py`.

## Context

Leer antes de implementar:

- `PRD.md:358-368` — las cinco tareas de la fase 5 y su salida comprobable.
- `PRD.md:222-223` — P0-07 (determinismo) y P0-08 (la tabla, sus denominadores y la
  declaración obligatoria sobre la capa 2 en el registro histórico).
- `PRD.md:225` — P0-09: otra persona reproduce preparación, pruebas y comparación.
- `PRD.md:231` — memoria: qué cuenta cada regla y cómo se actualiza el estado ante un
  bloqueo hipotético en la reproducción histórica.
- `PRD.md:164` — la expectativa escrita antes de evaluar: bloquear las 13.661 ediciones,
  incluida la primera de cada uno de los 3.099 IDs.
- `PRD.md:166` — lo que el corpus **no** mide: si el portero estorba. Esa mitad son los
  casos propios.
- `PRD.md:263-270` — §9, qué se mide en cada ámbito y con qué límites.
- `README.md:90-115` — las declaraciones de la capa de memoria (reloj simulado, H1 sybil,
  concurrencia) con las que la tabla tiene que ser coherente, sin repetirlas mal.
- `.claude/plans/phase-4-memory/plan.md` `## Notes` — los dos fallos que ninguna prueba
  pilló y cómo salieron.

Ficheros que se tocan:

- `bouncer/replay.py` — **CREATE**. Recorrido cronológico del corpus, registro por evento
  y resumen. No importa `bouncer.tools`.
- `bouncer/demo.py` — **CREATE**. Corre los cinco guiones y los dos recorridos, comprueba
  efectos y escribe `docs/results.md` y `docs/results-summary.json`.
- `tests/acceptance/test_replay.py` — **CREATE**, escrito a ciegas contra el contrato.
- `tests/unit/test_scaffolding.py` — **UPDATE**, sondas de andamiaje de esta fase.
- `.gitignore` — **ADD** `results/`.
- `README.md` — **UPDATE**: sección de fase 5, comandos verificados, estado de fases.
- `PRD.md:3-5` — **UPDATE** solo la línea de estado.
- `docs/results.md`, `docs/results-summary.json` — **CREATE**, generados.

Patrón a seguir: `bouncer/prepare.py` y `bouncer/executor.py` — funciones sueltas,
constantes arriba, dataclasses congeladas para lo que no cambia, `main(argv)` con argparse
y un JSON de resumen por stdout.

Avisos:

- `replay.py` **no importa `bouncer.tools`**. Es la garantía estructural de que nada del
  corpus se ejecuta; si alguien añade ese import, la prueba lo tumba.
- Ni cuerpos del corpus ni rutas del host en ningún registro.
- No se visita ninguna URL del corpus, ni se ejecuta ninguna instrucción suya.
- La política v1 no se toca. No se añaden reglas de memoria para conseguir bloqueos.
- No atribuir mejora histórica a la memoria: no la hay, y hay que decirlo con el número.
- Los cinco guiones de `scenario/scripts/` están congelados con sus `expect`. La fase 5
  los recorre, no los reescribe.
- **Lección de la fase 4: sondas de usar y tirar, no fiarse de la suite.** Los dos fallos
  serios de la fase anterior salieron probando a mano, no leyendo.

## Acceptance contract

- [ ] El recorrido produce una línea por evento, en el orden cronológico del fichero, con
      `rev_id`, `source_ref`, `agent_id`, `page_key`, `decision`, `rule`, `reason`,
      `policy_version`, `layers` — y sin `body`. 13.661 líneas para 13.661 filas.
      — `test_replay_logs_every_event`
- [ ] Con `--layers permissions` las 13.661 quedan bloqueadas por `default-deny`, y el
      resumen da la cantidad **y el denominador**. — `test_replay_blocks_every_edit`
- [ ] Con `--layers permissions,memory` las decisiones son idénticas una a una, y el
      resumen declara `clock-budget` no evaluable en el registro histórico con su razón.
      — `test_memory_changes_nothing_on_the_corpus`, `test_summary_declares_non_evaluable_rule`
- [ ] Dos recorridos con los mismos eventos y capas dan registros **byte a byte idénticos**;
      el tiempo de comprobación vive solo en el resumen. — `test_replay_is_deterministic`
- [ ] `bouncer/replay.py` no importa `bouncer.tools` ni ningún ejecutor de herramientas, y
      ningún cuerpo del corpus aparece en el registro. — `test_replay_never_executes`
- [ ] La demo enseña por llamada agente, llamada, decisión, regla y efecto; tras el guion
      de la edición prohibida, `saginaw-county.md` del `workdir` es byte a byte idéntico al
      de `scenario/wiki/`. — `test_demo_shows_effect_and_absence_of_effect`
- [ ] La demo escribe `docs/results.md` con dos bloques separados —registro histórico con
      denominador 13.661 / casos propios con autorización conocida—, con las cuatro filas
      del guion legítimo y la fila bloqueada etiquetada. — `test_results_table_has_both_blocks`
- [ ] El bloque de casos propios cuenta **tarea completada**, no solo llamadas: para el
      guion legítimo, rondas respondidas sobre rondas disponibles. La fila de `harness_bug`
      con memoria da 2 de 3, y la tabla dice que la respuesta que falta no se perdió, se
      sobreescribió. — `test_table_counts_rounds_not_only_calls`
- [ ] La tabla declara por escrito que en el registro histórico la capa 2 no aporta
      bloqueo, porque la primera llamada de cada agente ya cae en la capa 1.
      — revisión manual en `/verify`
- [ ] Cobertura de `bouncer/` ≥ 80 %.

Comandos que ejecutará `/verify`:

```sh
uv run pytest -q
uv run --with pytest-cov pytest -q --cov=bouncer --cov-report=term-missing
uv run python -m bouncer.replay --layers permissions --run-id verify-l1 --output-dir results/replay-l1
uv run python -m bouncer.replay --layers permissions --run-id verify-l1 --output-dir results/replay-l1-again
diff results/replay-l1/events.jsonl results/replay-l1-again/events.jsonl   # P0-07: idéntico byte a byte
uv run python -m bouncer.replay --layers permissions,memory --run-id verify-l12 --output-dir results/replay-l12
# P0-08: mismas decisiones con y sin memoria. Byte a byte no vale: cada línea lleva su
# propio campo `layers`, que es justamente lo que tiene que diferir. Sin jq: un juez
# reproduce con lo que ya declara pyproject.toml, nada más.
uv run python -c "
import json
key = lambda p: [(r['rev_id'], r['decision'], r['rule']) for r in map(json.loads, open(p))]
a, b = key('results/replay-l1/events.jsonl'), key('results/replay-l12/events.jsonl')
print('identical decisions:', a == b, '|', len(a), 'events')"
uv run python -m bouncer.demo --output-dir results/demo
git diff --check
```

## Out of scope

- Capas 3 (modelo) y 4 (entre agentes), y el estado `hold` con revisor.
- Reglas de memoria nuevas o cualquier cambio en la política v1.
- Arreglar H1 (sybil) o la concurrencia: declarados en la fase 4, siguen declarados.
- La matriz de nueve fases (P0-10) y el informe del sprint: entregable documental, aparte
  de esta numeración.
- Figuras y gráficas. P0-08 pide una tabla; una tabla se entrega.

## Interfaces

```
replay(events: Path, policy: Path, run_id: str, output_dir: Path,
       layers: tuple[str, ...] = ("permissions",)) -> Path      # devuelve el registro

# resumen, junto al registro y en docs/results-summary.json
{"run_id", "layers", "policy_version", "events": 13661, "decisions": {"block": 13661},
 "rules": {"default-deny": 13661}, "agent_ids": 3099,
 "memory_governed_events": 0,
 "non_evaluable_rules": [{"rule": "clock-budget", "reason": "..."}],
 "blocked_state_update": "...", "check_seconds_total": float, "check_us_per_call": float}
```

`replay` usa `decide` tal cual, sin tocar `gate.py`: la fase 5 no cambia el núcleo de
decisión, solo lo recorre desde otro sitio.

## Tasks

### T1. CREATE las pruebas, a ciegas

**Archivo:** `tests/acceptance/test_replay.py`. Un escenario por criterio del contrato,
escrito por un agente que solo ve el contrato y las interfaces de arriba. Corpus reducido
propio en `tmp_path`, no las 13.661 filas reales.

**Depende de:** nada. **VALIDATE:** `uv run pytest -q tests/acceptance/test_replay.py` en
RED.

### T2. CREATE `bouncer/replay.py`

Recorrido, registro por evento, resumen con denominadores y reglas no evaluables. Sin
pandas, sin importar herramientas.

**Depende de:** T1. **VALIDATE:** `uv run pytest -q tests/acceptance/test_replay.py` y los
dos comandos de recorrido de `/verify` con su `diff`.

### T3. CREATE `bouncer/demo.py`

Los cinco guiones × las capas que correspondan, los dos recorridos, comprobación de efecto
y ausencia de efecto, y generación de `docs/results.md` y `docs/results-summary.json`.

**Depende de:** T2. **VALIDATE:** `uv run python -m bouncer.demo --output-dir results/demo`
y las pruebas de la tabla.

### T4. Sondas de usar y tirar

Antes de dar por buena la fase: agente con `agent_id` repetido entre guiones, corpus con
una fila malformada, `--output-dir` dentro de `scenario/`, y recorrido con `--layers`
inválido. No fiarse de la suite.

**Depende de:** T3. **VALIDATE:** lo que salga se arregla con su prueba.

### T5. UPDATE documentación

`.gitignore` (`results/`), `README.md` (fase 5, comandos verificados, estado) y la línea de
estado de `PRD.md`. Revisión con especialista; hallazgos de seguridad a `security-reviewer`.

**Depende de:** T4. **VALIDATE:** los comandos de `/verify` otra vez.

## Notes

- **Desviación, paso uno (12-09-2026).** El plan daba la interfaz de `demo.py` escribiendo
  en `docs/` sin más. Le he añadido un parámetro `docs_dir` (`--docs-dir`, por defecto
  `docs`) antes de mandárselo al escritor ciego: sin él, cada ejecución de la prueba de
  aceptación sobreescribiría `docs/results.md` del repositorio con los números de un corpus
  de juguete. Es un parámetro para poder probar, no una capacidad nueva.

- **Enmiendas al escritor ciego (Adolfo, 12-09-2026: «arregla 1 y 2»).** Dos cosas que el
  escritor decidió y no le tocaban. (a) `test_table_counts_rounds_not_only_calls` exigía que
  toda entrada con `rounds_answered` valiese 3 salvo la bloqueada, lo que obligaba a que
  **solo** el guion legítimo llevase recuento de rondas — una decisión de alcance cerrada
  por accidente. Ahora el recuento se acota a las entradas con `script == "legitimate"`.
  (b) `test_replay_never_executes` prohibía la **cadena** `bouncer.tools` en el texto fuente,
  así que el módulo no podía ni mencionar la garantía en su propio docstring, y un import
  con alias se habría colado. Ahora analiza el árbol sintáctico y rechaza importaciones
  reales —absolutas, relativas o con alias—, no menciones en prosa.

- **Desviación, T3 (12-09-2026).** `BLOCKED_ROW_LABEL` decía «it cannot tell an honest waiter
  from a cheat». La prueba selecciona la fila del reloj honesto buscando `honest` en el texto
  de la fila, así que mi etiqueta hacía que esa búsqueda cazara dos filas. La prueba no está
  mal: selecciona por subcadena y yo metí la palabra en una celda. Cambiado a «good-faith
  waiter». **No se tocó la prueba.**

- **Fallo encontrado en T3 que ninguna prueba veía.** El recorrido paso a paso que imprime la
  demo salía de la **primera** ejecución de cada guion, que es la de capa 1 sola. Resultado:
  `wait_budget` se imprimía con sus tres esperas permitidas bajo el rótulo «chained waits are
  stopped by memory», y `two_agents` igual. El rótulo contradecía lo que el juez veía debajo.
  Ahora `WALKTHROUGH` indexa por `(guion, reloj, capas)` y se imprime la ejecución donde la
  afirmación es visible.

- **Fallo encontrado en T4, sondas de usar y tirar.** Una fila de corpus con `operation` sin
  punto (`"wikiedit"`) pasaba **en silencio**: se registraba con `tool="wikiedit"` y
  `operation=""` y se bloqueaba por default deny. La decisión era la segura, pero escribía una
  línea de registro afirmando una llamada con operación vacía, mientras que el resto de filas
  rotas fallan a gritos. Corregido en `read_events` y fijado con
  `test_replay_rejects_a_broken_corpus_row`. Las otras sondas aguantaron: fila sin `page_key`,
  `agent_id` no-cadena, capas inválidas, `--output-dir` dentro de `scenario/`, cuerpo nulo,
  líneas en blanco y corpus vacío (sin división por cero).

- **Añadido fuera del contrato: andamiaje para las dos CLI.** El escritor ciego avisó de que
  ningún criterio cubría `main()`. Cubiertas en `tests/unit/` (`test_replay_cli_prints_counts`,
  `test_demo_cli_writes_the_table_where_it_is_told`), no en aceptación: el contrato está
  congelado y esto es herramienta de trabajo, no examen.

- **Adolfo, 12-09-2026 — «rounds answered» solo donde el guion lo intenta.** La primera
  versión rellenaba la columna en los doce recorridos, así que `wait_budget`, `two_agents` y
  `unknown_operation` salían con «0 of 3» sin contener ni una `answer.submit`: se leía como un
  coste del portero y no lo era. Ahora un recorrido sin ninguna `answer.submit` no lleva las
  claves `rounds_answered`/`rounds_available` en el JSON y la tabla dice «not attempted».
  `forbidden_edit` sí las lleva (1 de 3): lo intentó y llegó hasta donde llegó. Esta es la
  decisión que la enmienda de la prueba dejó abierta a propósito.

- **Revisión con especialista y arreglos (Adolfo, 12-09-2026: «arregla todo lo necesario para
  que funcione bien»).** Un revisor único, a ciegas. 0 críticos, 2 altos, 7 medios, 6 bajos;
  ninguna prueba de aceptación debilitada; el árbol sin tocar. Arreglado todo lo que afectaba
  al funcionamiento o a la verdad de un número, con su repro comprobada después:
  - **A1, pérdida de datos.** `--output-dir data/prepared/wiki` **borraba el corpus**:
    `LOG_NAME` es `events.jsonl`, el mismo nombre que la entrada, y el registro se abría en
    modo `w` antes de leer la fuente. Verificado sobre copia: 40.347 bytes → 0, `"events": 0`
    y **código de salida 0**. Parecía un recorrido correcto de un fichero vacío. El ejecutor ya
    tenía la guardia análoga; el recorrido no. Ahora compara rutas resueltas y se niega.
    Comprobado: la entrada queda intacta.
  - **A2, denominador de rondas.** `rounds_available` era siempre `len(questions)`, así que
    `forbidden_edit` —que intenta una sola ronda por construcción— publicaba «1 of 3» sin
    etiqueta, justo debajo de un «2 of 3» que significa «esto lo costó el portero». Ahora el
    denominador es lo que **ese** guion intenta: lee `1 of 1`. Y la etiqueta de la fila
    bloqueada se condiciona a que exista un bloqueo real de `clock-budget` en esa ejecución,
    no a que el guion se llame `legitimate`.
  - **M3, el paso a paso mentía sobre el efecto.** Decía «the tool was not invoked» para una
    llamada **permitida** cuya herramienta lanzó, indistinguible de un veto. Ahora ramifica por
    `status` e imprime `error — invoked and failed: ...`. Comprobado forzando un
    `FileNotFoundError`; la ruta del host ya salía redactada a `<workdir>`.
  - **M4, la tabla no cuadraba.** `error` y `rejected` se contaban y se tiraban: con un fallo
    de herramienta salía `12 | 11 | 0`, y un fallo silencioso se leía como un coste **menor**.
    Añadidas las dos columnas y la frase de que la suma cuadra en toda fila.
  - **M5, conteo de reglas gobernadas.** `memory_rules_for` empareja por tool/operation antes
    de que los permisos hayan mirado los argumentos, y un contador global suprimía la
    declaración de no evaluable de **todas** las reglas. Corpus sintético: daba
    `memory_governed_events: 3` y `non_evaluable_rules: []` con `clock-budget` evaluada cero
    veces. Ahora se cuenta por regla y solo si la comprobación llegó a preguntarle; el mismo
    corpus da `0`, `{}` y declara `clock-budget`. Inalcanzable con el corpus de hoy, roto en
    cuanto llegue otro dataset.
  - **M6, la guardia de imports prometía más de lo que comprobaba.** La prueba congelada mira
    solo el AST de `replay.py`; un import transitivo (`from bouncer.executor import
run_script`) le daba las herramientas con todo en verde. Añadida
    `test_replay_cannot_reach_the_tools_even_transitively` en andamiaje: importa el módulo en
    un intérprete limpio y comprueba que `bouncer.tools` no aparece en `sys.modules`, **con
    caso de control** sobre `bouncer.demo` para demostrar que la sonda puede fallar. La prueba
    congelada no se tocó. README corregido para decir lo que de verdad se comprueba.
  - **M7, frase falsa en un entregable versionado.** `blocked_state_update` decía «state is
    updated after an allow and never after a block», y el recorrido tampoco actualiza tras un
    `allow`. Reescrita para describir lo que el recorrido hace.
  - **M1/M2 y bajos.** README citaba 0,68 µs contra 0,739 de la tabla: retirado el número de la
    prosa, que ahora remite a la tabla. Añadida la frase de que los dos tiempos son muestras
    únicas y su diferencia es ruido. `newline="\n"` en registro y resumen, para que el
    determinismo valga en cualquier máquina y no solo en esta. Una línea JSON malformada da
    ahora `path:línea` como el resto de validaciones. La tabla declara las 930 filas excluidas
    y remite a `cleaning.json`. Corregida la mezcla de denominadores del README («12 calls» /
    «11 calls»).
  - **No arreglado, por ser presentación:** las dos aserciones vacías del fichero congelado
    (`"1" in blocked_row` la satisface el `11`), y la ausencia de una prueba sobre las 13.661
    filas reales. Anotadas en el informe de revisión.
  - **Falso positivo del revisor, causado por mi empaquetado:** marcó la cobertura como no
    verificable porque `pytest-cov` no está en `pyproject.toml`. No le pasé el bloque de
    comandos de `/verify`, que usa `uv run --with pytest-cov`. Medido: 97 %.

- **Resultados verificados (12-09-2026, antes de la revisión).** 71/71 pruebas verdes en 0,56 s. Cobertura 99 %
  (`demo.py` 98 %, `replay.py` 97 %, resto igual o mejor). Corpus: 13.661 eventos, 13.661
  bloqueos por `default-deny`, 3.099 identidades, 0,68 µs por comprobación, cero eventos
  gobernados por una regla de memoria. Determinismo: dos recorridos byte a byte idénticos.
  Capa 1 frente a 1+2 sobre el corpus: decisiones idénticas en los 13.661.

- **Renombrado de vocabulario (Adolfo, 12-09-2026: «de qué sirve tener una tabla si no la
  entiende»).** La tabla usaba identificadores que no se entienden sin explicación:
  `legitimate` chocaba con `honest`, `harness_bug` es jerga interna, y `permissions` vs
  `memory` sonaba a dos módulos en vez de a la tesis del proyecto. Objeté una vez por el
  coste (desbloquear pruebas congeladas) y **Adolfo ordenó hacerlo igualmente, incluidas las
  dos que el PRD prohíbe tocar**: la clave `memory_rules` de la política v1 y el id de la
  regla `clock-budget`. Queda escrito aquí como orden suya y como incumplimiento consciente
  de `PRD.md:229` («una sola versión, fijada antes de evaluar»). Adolfo creó
  `.claude/plans/.unlock-tests`; las cinco pruebas congeladas se editaron con ese permiso.

  | Antes                                                  | Ahora                                                     |
  | ------------------------------------------------------ | --------------------------------------------------------- |
  | `permissions` · `memory`                               | `per_call` · `per_history`                                |
  | `harness_bug` · `honest`                               | `clock_runs_ahead` · `clocks_matched`                     |
  | `legitimate`                                           | `authorized_work`                                         |
  | `forbidden_edit`                                       | `page_write`                                              |
  | `unknown_operation`                                    | `unlisted_tool`                                           |
  | `wait_budget`                                          | `chained_waits`                                           |
  | `memory_rules:` (política)                             | `history_rules:`                                          |
  | `clock-budget` (id de regla)                           | `wait-costs-real-time`                                    |
  | `MemoryView`, `memory_state`, `memory_governed_events` | `HistoryView`, `history_state`, `history_governed_events` |

  Alcanzó a los 4 módulos, las 5 pruebas de aceptación, el andamiaje, los 4 ficheros de
  guion (renombrados con `git mv`), la política y el README.
  - **El PRD también, por orden de Adolfo.** En el PRD «memory» y «permissions» aparecen con
    dos sentidos: el nombre de la capa y la palabra inglesa corriente. Se cambiaron los 21
    usos que nombran la capa (incluidos los títulos de P0-04, P0-08, la fase 4, el nodo del
    diagrama y la tabla de capas, que ahora llevan `per_call`/`per_history` entre comillas
    invertidas). **Cero ocurrencias de «memory» quedan en el PRD.** Se conservaron a
    propósito los 8 «permissions» que significan permisos de acceso y no la capa —«authorized
    instructions and permissions in force per call», «collaboration permissions between
    agents», «restricting credentials and permissions»—, y todos los «legitimate», que son
    inglés normal («legitimate work»), no identificadores.
  - **Dos fallos míos durante el renombrado, encontrados y corregidos:** (a) mi regla solo
    cubría comillas dobles, y `run['memory_governed_events']` en un f-string con comillas
    simples sobrevivió — lo cazó la suite con un `KeyError`; (b) `conftest.py` fabricaba una
    política con `memory_rules:`, que `gate.py` ya no lee: esas pruebas se habrían quedado
    **sin regla de historial y en verde**. Ese segundo lo cacé con un grep, no con la suite.
  - **Verificación:** barrido `grep` de los ocho nombres viejos en todo el repositorio →
    limpio. 72/72 verdes. Datos viejos borrados (`results/`, `docs/results.md`,
    `docs/results-summary.json`) y todo regenerado desde cero.

- **Resultados verificados tras los arreglos (12-09-2026).** 72/72 pruebas verdes en 0,59 s.
  Cobertura 97 % (`demo.py` 92 %, `replay.py` 92 %, resto igual o mejor; baja respecto al 99 %
  porque los arreglos añadieron ramas de error que ninguna prueba recorre). Corpus: 13.661
  eventos, 13.661 bloqueos, 3.099 identidades, cero gobernados por regla de memoria.
  Determinismo byte a byte y decisiones idénticas entre capas, otra vez. `git diff --check`
  limpio.
