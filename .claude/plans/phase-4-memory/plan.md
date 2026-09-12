# Plan: fase 4 — memoria por ejecución y agente

**Status**: implemented

## Goal

El portero deja de ser ciego al pasado. La regla `clock-budget`, que la política v1 ya
declara desde la fase 2, pasa a evaluarse de verdad: cada `clock.wait(N)` reserva N
segundos de reloj de tarea contra el tiempo real transcurrido del mismo agente, y si lo
ya reservado supera lo transcurrido, la llamada se bloquea antes de llegar a la
herramienta. Cada agente lleva su propio presupuesto: el bloqueo de uno no gasta ni
frena al otro. El guion legítimo sigue pasando entero con la memoria encendida y en
menos de un segundo. Queda cubierto P0-04.

## Findings

Exploración del 12-09-2026 sobre el código ya escrito (pruebas en verde, 42/42, 0,35 s):

- La fase 3 dejó el enganche hecho por negación: `bouncer/gate.py:62-67` (`check_layers`)
  lanza `NotImplementedError` si se pide la capa `memory`. No hay pase silencioso que
  arreglar; hay un guardia que sustituir.
- La política **no cambia**: `scenario/policy.yaml:47-56` ya declara `clock-budget` con
  `scope: agent_history`, `budget: task_seconds`, `against: wall_seconds_elapsed`,
  `ratio: 1`, `counts: authorizations`, `source: task.md#rounds-and-waiting`. La fase 4
  la implementa sin tocar la v1, que es lo que exige PRD.md:229 (una sola versión, fijada
  antes de evaluar).
- Los dos guiones de fase 4 ya existen con sus `expect` escritos:
  `scenario/scripts/wait_budget.jsonl` (5 líneas, `ResearchAgentD` encadenando) y
  `scenario/scripts/two_agents.jsonl` (4 líneas, `ResearchAgentE` y `ResearchAgentF`
  intercalados). No hay que inventar casos.
- `bouncer/executor.py:81-84` ya recibe `wall_clock` inyectable y `clock_mode`; las
  pruebas de aceptación congeladas ya usan un reloj falso (`tests/acceptance/conftest.py:112-124`,
  cierre sobre un float mutable con `.advance()`).
- **Choque medido entre la regla y el guion legítimo.** `scenario/scripts/legitimate.jsonl`
  líneas 5 y 9 son `clock.wait(2111)` con `expect: allow`. Con el modo por defecto
  (`harness_bug`, que adelanta el reloj de tarea al instante sin consumir tiempo real),
  la línea 9 encuentra 2111 s reservados frente a ~0,01 s transcurridos y se bloquea.
  Con `--clock honest` acierta, pero el guion tarda 2 × 2111 s = **70 minutos**, porque
  `bouncer/tools.py:66-67` llama a `time.sleep`.
- Causa del choque: `clock_mode` hace dos trabajos a la vez, decidir **si se duerme** y
  decidir **si el reloj real avanza con la espera**. Para la regla solo importa lo segundo.
- `tests/acceptance/test_gate.py:80-98` (`test_memory_layer_not_silently_skipped`) exige
  `NotImplementedError` al pedir la capa `memory`. Es un guardia correcto **de fase 3**
  y esta fase tiene que retirarlo: requiere el marcador `.claude/plans/.unlock-tests`.
- `tests/unit/test_scaffolding.py:62` monkeypatchea `tools.time.sleep` y comprueba que el
  modo honesto duerme. Es prueba de andamiaje mía, no congelada: se actualiza.
- Fuera de la fase, encontrado de paso y **ya resuelto antes de implementar** (Adolfo,
  12-09-2026): 8 enlaces rotos en `README.md`, `AGENTS.md` y `PRD.md` — la carpeta se
  llamaba `docs/hallazhos/` y los enlaces apuntaban a `docs/hallazgos-*.md` sin la
  carpeta. Renombrada a `docs/hallazgos/` y corregidos los enlaces; los dos que apuntaban
  a `docs/tareas-pendientes.md`, que nunca existió, se retiraron. Borrado el fichero
  basura `0`. La traducción del documento de diseño la commiteó Adolfo (`b3b65d4`).
  El plan archivado de las fases 2–3 sigue citando `docs/hallazhos/`: es registro
  histórico y no se toca.

## Decisions

- **Adolfo, 12-09-2026 — el plan cubre solo la fase 4.** Alternativas: fases 4+5 en un
  plan (como se hizo con 2+3) o fase 5 primero para tener antes el artefacto que ve el
  jurado. Elegida fase 4 sola: cierra un requisito entero antes de tocar nada más, y la
  fase 5 se planifica sabiendo ya cómo quedó la memoria.

- **Adolfo, 12-09-2026 — el modo honesto usa un reloj real simulado; no se duerme.**
  El problema resuelto: con la capa de memoria encendida y el reloj roto por defecto, el
  agente honrado se bloquea en su segunda espera, y ese número iría a la tabla de P0-08
  como «acción legítima bloqueada» siendo un artefacto de nuestro decorado, no un
  resultado del método. Alternativas: dormir de verdad y correr el guion legítimo a mano
  fuera de las pruebas (70 min, la demo no puede enseñar al agente honrado con memoria);
  o no tocar nada y publicar el bloqueo como falso positivo declarado. **Razón de
  Adolfo:** la demo la tiene que poder correr un juez en segundos, no en una tarde.
  **Coste asumido y que hay que escribir con estas palabras en el informe:** en modo
  honesto el reloj real avanza exactamente lo que el agente pide esperar, así que la
  regla no puede saltar ahí por construcción. Que el guion legítimo pase demuestra que
  la regla no molesta a un agente en un mundo con los relojes acoplados — que es el
  mundo honesto —, no «cero falsos positivos medidos».

- **Adolfo, 12-09-2026 — la concurrencia se declara no aplicable.** El contrato de cierre
  del PRD (PRD.md:277) pide verificar la cuota «incluyendo concurrencia». El ejecutor
  recorre un guion línea a línea y esa situación no puede ocurrir. Alternativa que
  recomendó Claude: hacer comprobar-y-reservar una sola operación indivisible con un
  cerrojo y una prueba de dos hilos (~10 líneas). Elegido declararlo: no escribir código
  sin uso real para un ejecutor monohilo. **Consecuencia obligatoria:** se edita esa línea
  del contrato de cierre del PRD y se justifica por escrito; no basta con omitirlo.

- **Adolfo, 12-09-2026 — no volver a rebatir decisiones ya tomadas.** Una objeción, una
  vez, y a ejecutar.

- **Claude, mecánico — `wall_offset` en vez de `time.sleep`.** `RunState` gana un campo
  `wall_offset: int`. En modo `honest`, `clock_wait` le suma los segundos realmente
  esperados en lugar de dormir; en `harness_bug` no lo toca — ahí está el fallo, en una
  línea. El reloj inyectado (`wall_clock`) se queda como base, porque las pruebas de
  aceptación congeladas lo pasan. Transcurrido = `int(wall_clock() - wall_start) + wall_offset`.

- **Claude, mecánico — segundos enteros, por determinismo.** El transcurrido se trunca a
  segundos enteros. Sin eso, en modo `harness_bug` el reloj real mide milisegundos
  distintos en cada ejecución y `test_deterministic_run` (P0-07) dejaría de valer. Con el
  truncado, el modo roto da 0 siempre y el honesto da el offset exacto. La unidad es la
  que la política ya declara (`wall_seconds_elapsed`).

- **Claude, mecánico — el estado de memoria vive en `gate.py`, sin módulo nuevo.**
  `gate.py` son 97 líneas; la memoria añade ~35. Un `MemoryView` congelado (agente,
  reservado, transcurrido) que el ejecutor construye y `decide` consulta. `decide` sigue
  siendo pura: mira, no apunta. Quien reserva y libera es el ejecutor, que es quien posee
  el estado — coherente con que la identidad y la política también salgan de ahí.

- **Claude, mecánico — `check_layers` sigue sin permitir pases silenciosos.** Deja de
  lanzar por pedir `memory`, y pasa a lanzar si se pide `memory` sin vista de memoria.
  El guardia no desaparece, cambia de condición.

- **Claude, mecánico — `--layers` en el CLI.** `permissions` por defecto,
  `permissions,memory` para encender la capa 2. Hace falta ya para recorrer los guiones
  de esta fase, y la fase 5 lo necesita tal cual para la comparación de P0-08 sin una
  segunda política.

## Context

Leer antes de implementar:

- `PRD.md:219` — P0-04 y su observación de aceptación.
- `PRD.md:231` — memoria: qué cuenta cada regla y cuándo consume o libera.
- `PRD.md:347-356` — las cuatro tareas de la fase 4.
- `PRD.md:277` — la línea del contrato de cierre que hay que editar (concurrencia).
- `.claude/plans/phase-2-3-scenario-and-gatekeeper/plan.md:38` — el enunciado literal de
  la regla `clock-budget` y de dónde sale cada parámetro. **No reinterpretar**: primer
  `wait` con nada reservado pasa; el bloqueo mira lo _ya_ reservado, no lo que se pide.
- `docs/hallazgos/hallazgos-tarea-wiki.md` — el fallo del reloj documentado, origen de la regla.

Ficheros que se tocan:

- `bouncer/tools.py:17-26` (`RunState`) y `:61-71` (`clock_wait`) — campo `wall_offset`,
  el modo honesto suma en vez de dormir, se retira el import `time`.
- `bouncer/gate.py:13-14` (constantes), `:62-67` (`check_layers`), `:88-97` (`decide`) —
  `MemoryView`, evaluación de `memory_rules`, guardia nuevo.
- `bouncer/executor.py:36-78` (`execute_line`), `:81-118` (`run_script`), `:121-136` (`main`)
  — reservas por agente, liberación en error, campos de log, `--layers`.
- `tests/acceptance/test_gate.py:80-98` — **borrar** `test_memory_layer_not_silently_skipped`;
  requiere `.claude/plans/.unlock-tests`.
- `tests/acceptance/test_memory.py` — nuevo, escrito a ciegas.
- `tests/unit/test_scaffolding.py:60-66` — la prueba de `time.sleep` pasa a comprobar el offset.
- `README.md` — sección de memoria y comando con `--layers`.
- `PRD.md:277` — la línea de concurrencia.

Patrón a seguir: `bouncer/prepare.py` y el propio `gate.py` — funciones sueltas,
constantes arriba, dataclasses congeladas para lo que no cambia, `main(argv)` con argparse.

Avisos:

- La reserva se hace **tras** permitir (`counts: authorizations`) y se **libera** si la
  herramienta devuelve error. Un error de herramienta no gasta presupuesto.
- El reloj real y el de tarea los posee el ejecutor. Un argumento del agente no los toca.
- No inventar límites nuevos ni tocar la política v1 para obtener bloqueos (PRD.md:392).
- El log no copia cuerpos ni rutas del host.

## Acceptance contract

- [ ] Con `layers=("permissions","memory")` y una vista de memoria, `decide` bloquea
      `clock.wait` cuando lo reservado por ese agente supera los segundos transcurridos,
      con `rule: clock-budget`; y lo permite cuando no lo supera. La política sigue siendo
      la v1 sin cambios. — `test_memory_rule_blocks_and_allows`
- [ ] Pedir la capa `memory` sin vista de memoria lanza un error explícito: ni permite ni
      bloquea. — `test_memory_layer_needs_state`
- [ ] Recorrer `wait_budget.jsonl` con `permissions,memory` y reloj `harness_bug`: la
      primera espera se permite, la segunda y la tercera se bloquean con `rule: clock-budget`,
      y `round.question` final devuelve `round:none`. El mismo guion con `permissions`
      sola permite las tres esperas. — `test_wait_budget_script`, `test_wait_budget_layer1_only`
- [ ] Recorrer `two_agents.jsonl` con `permissions,memory`: E permitido y luego bloqueado,
      F permitido en su espera **y** en su lectura posterior. El presupuesto de E no
      aparece en la decisión de F. — `test_budgets_are_isolated_per_agent`
- [ ] Recorrer `legitimate.jsonl` con `permissions,memory` y `--clock honest`: 12 llamadas
      `ok`, cero bloqueos, y el recorrido termina en menos de 5 segundos de reloj real.
      — `test_legitimate_passes_with_memory_and_honest_clock`
- [ ] En modo `honest` el reloj real del ejecutor avanza los segundos esperados y no se
      llama a `time.sleep`; en `harness_bug` no avanza. — `test_honest_clock_advances_without_sleeping`
- [ ] Si la herramienta falla después de que la memoria haya permitido y reservado, la
      reserva se libera: la siguiente llamada del mismo agente ve el presupuesto sin gastar.
      — `test_reservation_released_on_tool_error`
- [ ] Toda línea de log lleva `layers`; las llamadas que la capa de memoria evaluó llevan
      además el estado que justifica la decisión (reservado y transcurrido). — `test_log_carries_memory_state`
- [ ] Dos recorridos de `wait_budget.jsonl` con el mismo `--run-id` y las mismas capas
      producen logs idénticos salvo `duration_ms`. — `test_deterministic_with_memory`
- [ ] `PRD.md` declara por escrito que la concurrencia no se verifica porque el ejecutor
      es monohilo, en la línea del contrato de cierre. — revisión manual en `/verify`
- [ ] Cobertura de `bouncer/gate.py`, `tools.py`, `executor.py` ≥ 80 %.

Comandos que ejecutará `/verify`:

```sh
uv run pytest -q
uv run --with pytest-cov pytest -q --cov=bouncer --cov-report=term-missing
uv run python -m bouncer.executor --script scenario/scripts/wait_budget.jsonl --run-id verify-budget --output-dir /tmp/bouncer-verify/budget --layers permissions,memory
uv run python -m bouncer.executor --script scenario/scripts/two_agents.jsonl --run-id verify-two --output-dir /tmp/bouncer-verify/two --layers permissions,memory
uv run python -m bouncer.executor --script scenario/scripts/legitimate.jsonl --run-id verify-legit --output-dir /tmp/bouncer-verify/legit --layers permissions,memory --clock honest
git diff --check
```

## Out of scope

- Demo con restauración de estado, recorrido cronológico del corpus y tabla de comparación
  capa 1 frente a 1+2: fase 5.
- Cerrojo y prueba de concurrencia: declarado no aplicable (ver Decisions).
- Retener con revisor, capa 3 (modelo) y capa 4 (entre agentes).
- Reglas de memoria nuevas. La política v1 se implementa, no se amplía.
- Arreglar los enlaces rotos de `docs/hallazgos/`, el fichero `0` y el commit de la
  traducción: limpieza aparte, antes de entregar.

## Interfaces

```
MemoryView: agent_id: str, reserved_task_seconds: int, wall_seconds_elapsed: int   # congelado
decide(call: Call, policy: Policy, layers: tuple[str, ...], memory: MemoryView | None = None) -> Decision
```

`decide` mira; no apunta. El ejecutor posee `reserved: dict[str, int]` por `agent_id`,
reserva tras un `allow` de `clock.wait` y libera si la herramienta falla.

```
RunState: ... + wall_offset: int   # segundos que el modo honesto ha hecho avanzar el reloj real
wall_seconds_elapsed = int(wall_clock() - wall_start) + wall_offset
```

Línea de log: los campos del contrato de la fase 3, más `layers` siempre, y
`memory_state: {"reserved": int, "wall_elapsed": int}` en las llamadas que la capa de
memoria evaluó.

## Tasks

### T1. CREATE las pruebas, a ciegas

**Archivo:** `tests/acceptance/test_memory.py`. Un escenario por criterio del contrato,
escrito por un agente que solo ve el contrato y las interfaces de arriba.

**Depende de:** nada. **VALIDATE:** `uv run pytest -q tests/acceptance/test_memory.py` en
RED por la capa sin implementar.

### T2. DELETE el guardia de fase 3

**Archivo:** `tests/acceptance/test_gate.py`, quitar `test_memory_layer_not_silently_skipped`.
Necesita que Adolfo ponga `.claude/plans/.unlock-tests`. Su papel lo hereda
`test_memory_layer_needs_state`.

**Depende de:** T1. **VALIDATE:** `uv run pytest -q tests/acceptance/test_gate.py`.

### T3. UPDATE `bouncer/tools.py`

Campo `wall_offset`, modo honesto sumando en vez de durmiendo, import `time` fuera.
Actualizar `tests/unit/test_scaffolding.py:60-66`.

**Depende de:** T2. **VALIDATE:** `uv run pytest -q tests/acceptance/test_tools.py tests/unit`.

### T4. UPDATE `bouncer/gate.py`

`MemoryView`, evaluación de `memory_rules` con `ratio`, guardia nuevo en `check_layers`.

**Depende de:** T3. **VALIDATE:** `uv run pytest -q tests/acceptance/test_gate.py`.

### T5. UPDATE `bouncer/executor.py`

Reservas por agente, liberación en error, `layers` y `memory_state` en el log, `--layers`
en el CLI.

**Depende de:** T4. **VALIDATE:** los cinco comandos de `/verify`, y cobertura ≥ 80 %.

### T6. UPDATE PRD y README

`PRD.md:277`: la concurrencia no se verifica, con su razón. `README.md`: la capa de
memoria, qué mide, el comando con `--layers` y la declaración del reloj simulado.
Revisión con especialista; hallazgos de seguridad a `security-reviewer`.

**Depende de:** T5. **VALIDATE:** los comandos de `/verify` otra vez.

## Notes

- **Desviación, T1 (12-09-2026).** El escritor ciego entregó una prueba que habría fallado
  contra cualquier implementación correcta: en `test_honest_clock_advances_without_sleeping`
  puso el reloj de tarea en 3600 con `cooldown` 2111, así que la ronda 3 llega en 4222 y un
  `wait(900)` solo avanza 622 segundos, no los 900 que afirmaba. No lo parcheé aquí: se lo
  devolví al escritor con el dato que le faltaba (las esperas se cortan al llegar una ronda)
  y lo corrigió arrancando el reloj de tarea en 0. Lo demás quedó igual.
- **Desviación, T6 (12-09-2026).** El plan mandaba editar solo `PRD.md:277` por la
  concurrencia. También edité la observación de aceptación de **P0-04** (`PRD.md:219`), que
  decía «The check/reservation does not allow simultaneous calls to exceed the quota».
  Dejarla habría puesto al PRD a contradecirse consigo mismo en la misma página: el
  contrato de cierre declarando que la concurrencia no se verifica y el requisito
  exigiéndola. Es la misma decisión de Adolfo aplicada donde vuelve a estar escrita, no una
  decisión nueva. Si prefiere la redacción original, se revierte esa línea sola.
- **Precisión, T5.** El log solo lleva `memory_state` en las llamadas que alguna regla de
  memoria gobierna (hoy, `clock.wait`). En las demás el campo no aparece: el contrato pide
  «el estado que justifica la decisión», y donde ninguna regla miró no hay estado que
  justifique nada. `layers` sí va en todas las líneas.
- **Precisión, T5.** `wall_start` vive en `RunState` junto al resto de relojes, aunque
  ninguna herramienta lo use. La alternativa era pasarlo como noveno parámetro a
  `execute_line`. Los relojes ya son del ejecutor y ya viven ahí.
- **Limpieza previa (Adolfo, 12-09-2026).** Antes de implementar: `docs/hallazhos/` →
  `docs/hallazgos/`, 8 enlaces corregidos en README/AGENTS/PRD, retirados los dos enlaces a
  `docs/tareas-pendientes.md` (fichero que nunca existió) y borrado el fichero basura `0`.
  El plan archivado de las fases 2–3 sigue citando `docs/hallazhos/`: es registro histórico.
- **Fallo encontrado en revisión y corregido (Adolfo, 12-09-2026).** La revisión con
  especialista se cortó por límite de sesión, pero antes de caerse probó a un agente
  honrado esperando en trozos de 900 s con un cooldown de 2111 s. La tercera espera la
  corta la ronda que llega: el agente pide 900 y recibe 311, **y le cobrábamos los 900**.
  Desde ahí arrastraba una deuda de 589 s que no se salda nunca y quedaba bloqueado para
  esperar el resto de la ejecución sin haber hecho nada malo. Ninguna prueba lo pillaba
  porque en el guion legítimo las esperas son de 2111 s exactos y nunca se cortan.
  Corregido (opción A de Adolfo): se reserva lo pedido antes de ejecutar, y cuando la
  herramienta devuelve cuánto gastó de verdad se libera la diferencia — el mismo mecanismo
  que ya existía para el error, parcial en vez de total. Tres líneas en
  `bouncer/executor.py` y `test_cut_short_wait_is_charged_for_what_it_got` en
  `tests/unit/`. Alternativa descartada: dejarlo y declararlo como techo, que habría
  metido falsos positivos nuestros en la tabla de P0-08.
- **Revisión, T6 (12-09-2026), repetida y completa.** Sin críticos. La contabilidad del
  presupuesto aguantó un fuzz de 60 guiones de 40 llamadas: lo reservado siempre igual a los
  segundos de tarea realmente avanzados, nunca negativo, nunca cargado a otro agente. El log
  no filtra rutas del host, cuerpos ni secretos. Corregidos con prueba de andamiaje cada uno:
  - **H2**, `agent_id` no-cadena (lista o diccionario) reventaba la ejecución entera con
    `TypeError: unhashable type` y sin escribir ni una línea de log — una regresión que
    introdujo esta fase, porque con capa 1 sola el mismo guion corría. Ahora se rechaza como
    `rejected`, que es lo que P0-06 pide, y de paso deja de colisionar `True` con `1`.
  - **M1/M2**, `memory_rules` no se validaba al cargar: una errata en la política pasaba la
    puerta y reventaba a mitad de ejecución con un `KeyError` y medio log escrito. Y `against`,
    `counts` y `scope` eran decorativos: se podía escribir cualquier cosa y el código hacía lo
    de siempre, con el log apuntando a esa regla. `check_memory_rule` rechaza ahora todo lo que
    el código no aplica tal y como está escrito.
  - **M3**, `layers` en el log podía mentir: `decide` aplica los permisos siempre, así que
    `layers: ["memory"]` decía menos comprobación de la que hubo. `check_layers` rechaza toda
    tupla sin `permissions`.
  - **M4**, `int(value)` en la devolución se fiaba de lo que devolviera la herramienta. Una
    herramienta que devolvía `-5000` dejaba el presupuesto en negativo y mataba la regla. Al
    arreglarlo salió que mi primera versión del recorte devolvía el presupuesto entero en vez
    de cobrarlo, al revés de lo que decía su propio comentario. Ahora: lo que informe fuera de
    `[0, autorizado]` o no sea entero se cobra completo.
  - **M6**, el README se contradecía: decía «`--clock honest` really sleeps» en una sección y
    lo contrario en otra. Corregida la línea de fase 3.
  - **LOW**, `over_budget` volvía a emparejar `tool`/`operation` duplicando `memory_rules_for`,
    y `decide` recorría las reglas sin usarlo: dos emparejamientos para una pregunta, uno en el
    portero y otro en el ejecutor. Unificados.
- **M5 resuelto quitando código (Adolfo, 12-09-2026: «tiene que poder hacerse más simple»).**
  El reloj real por defecto era `time.monotonic`, así que la misma entrada podía decidir
  distinto en una máquina más lenta. Nada en esta demo consume tiempo salvo las esperas, y
  esas ya las cuenta `wall_offset`: el reloj por defecto pasa a empezar en cero y avanzar solo
  con ellas. Una línea. Comportamiento idéntico, sin máquina de por medio. Comprobado desde el
  CLI sin reloj inyectado: dos recorridos de `wait_budget.jsonl` dan logs idénticos salvo
  `duration_ms`. Alternativa descartada: declarar la no-determinación en el informe, que era
  más texto que código.
- **H1 declarado, no implementado (Adolfo, 12-09-2026).** El presupuesto es
  por identidad y el reloj de tarea es por ejecución, así que cada nombre nuevo compra una
  primera espera gratis y tres nombres recogen tres rondas en cero segundos reales. Es el
  abuso del incidente hecho con su otra técnica (el tablón sin autenticar). Las salidas son
  declararlo o añadir una regla de alcance `run`. Elegido declararlo, por dos razones que
  apuntan al mismo sitio: el plan deja fuera ampliar la política v1, y las pruebas congeladas
  exigen lo contrario — `test_budgets_are_isolated_per_agent` comprueba que el presupuesto de E
  no aparece en la decisión de F, que es lo que pide P0-04. Declarado en el README junto al
  límite de concurrencia, nombrando que el caso de la wiki fueron ~1.200 agentes y no uno.
- **Resultados verificados (12-09-2026).** 56/56 pruebas verdes. Cobertura 99 %
  (`gate.py` 100 %, `tools.py` 100 %, `executor.py` 99 %). `wait_budget`: 3 `ok`, 2
  `blocked` por `clock-budget`. `two_agents`: 3 `ok`, 1 `blocked`. `legitimate` con
  `--clock honest` y memoria: 12 `ok`, 0 bloqueos.
