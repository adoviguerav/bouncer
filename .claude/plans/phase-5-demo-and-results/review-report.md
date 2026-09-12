# Revisión — fase 5 (demo, reproducción histórica y resultados)

**Fecha:** 12-09-2026. **Revisor:** uno, `code-reviewer`, a ciegas (plan sin `## Notes`,
reglas del proyecto, requisitos P0 y las 952 líneas de diff pegadas literalmente).
**Manipulación del árbol:** ninguna. `git status --porcelain` antes y después coincide salvo
el `git add -A -N` que hice yo para construir el paquete. Corpus intacto, 13.661 líneas.

## Resumen en tres líneas

La afirmación central se sostiene: `replay.py` no puede ejecutar nada del corpus, y no por
disciplina sino por construcción — no hay `eval`, `exec`, `subprocess`, `importlib`, socket
ni HTTP en todo el camino, y el `body` del corpus solo llega a `Call.args`, que `decide`
nunca lee. Ninguna prueba de aceptación quedó debilitada. **Pero hay un camino de pérdida de
datos que destruye el entregable de la fase 1 en silencio**, y una columna de la tabla que
un jurado puede leer al revés. Lo primero que hay que arreglar es el borrado del corpus.

**Recuento: 0 críticos · 2 altos · 7 medios · 6 bajos.**

## ALTO

### A1. `replay` trunca su propia entrada si `--output-dir` es la carpeta del corpus — CONFIRMADO, pérdida de datos

`LOG_NAME = "events.jsonl"` es el mismo nombre que el `EVENTS_FILE` por defecto, y
`log_path.open("w")` se ejecuta **antes** de que `read_events` abra la fuente.

```sh
uv run python -m bouncer.replay --output-dir data/prepared/wiki --run-id x
```

**Verificado por mí también**, sobre una copia de 50 filas: el fichero de entrada pasó de
40.347 bytes a **0**, el resumen informó `"events": 0` y el proceso salió con código **0**.
Parece un recorrido correcto de un corpus vacío.

Refutación intentada y fallida: `executor.run_script` ya bloquea la equivalencia análoga
(`output_dir must not be inside the scenario`), así que el proyecto ya trata esta clase de
error como digna de guardia. `replay` no tiene ninguna. La tarea T4 del plan listaba
`--output-dir` dentro de `scenario/` como sonda, así que el caso se miró y se entregó sin
guardia — lo probé sobre el ejecutor, no sobre el recorrido.

**Arreglo sugerido:** comparar rutas resueltas antes de abrir el registro, o reutilizar la
guardia del ejecutor.

### A2. `rounds_available` es siempre `len(questions)`, así que `forbidden_edit` publica «1 of 3» en la columna donde «2 of 3» significa que la regla costó una ronda — CONFIRMADO

`run_one` cuelga `rounds_answered`/`rounds_available` de cualquier guion que llame a
`answer.submit`, con denominador fijo 3. `forbidden_edit` intenta una sola ronda **por
construcción**, así que sus dos filas leen `1 of 3` — y `note` está condicionado a
`script == "legitimate"`, así que nada las etiqueta.

En `docs/results.md` un jurado lee, en la misma columna: `legitimate 3 of 3`,
`legitimate+memory 2 of 3 (limit of the rule)`, `forbidden_edit 1 of 3 (—)`. La semántica
establecida de un déficit en esa columna es «esto lo costó el portero», y el de
`forbidden_edit` no lo es.

Refutación intentada y fallida: el comentario del propio código defiende exactamente ese
argumento para el caso cero — la guardia se queda una fila corta. Ningún número es
literalmente falso, por eso es ALTO y no crítico, pero es la lectura equivocada más probable
del entregable.

## MEDIO

- **M1. El README cita 0,68 µs y la tabla dice 0,739 y 0,726.** CONFIRMADO. Copiado a mano de
  una sonda anterior. Dos documentos que lee el jurado se contradicen.
- **M2. Dos tiempos a nivel de ruido publicados uno al lado del otro.** El recorrido que hace
  _menos_ trabajo mide más lento. Nada en la tabla dice que son medidas de una sola muestra;
  un lector puede concluir que la capa de memoria es gratis o de coste negativo.
- **M3. El recorrido paso a paso dice «the tool was not invoked» cuando la herramienta sí se
  invocó y falló.** CONFIRMADO con repro. `print_walkthrough` usa
  `result_ref or "no effect..."` y nunca imprime `status`. Una llamada permitida cuya
  herramienta lanza no tiene `result_ref`, así que sale `allow` + «no se invocó», que es una
  contradicción en pantalla e indistinguible de un bloqueo. Latente hoy (ningún guion falla).
- **M4. `error` y `rejected` se cuentan y luego se tiran de la tabla.** CONFIRMADO. Con un
  error de herramienta sale `12 | 11 | 0`, y 11 + 0 ≠ 12 sin nada que lo explique. Un fallo
  silencioso de herramienta se lee como un coste **menor**. Los números están en el JSON; el
  markdown, que es lo que se lee, los esconde.
- **M5. `memory_governed_events` cuenta reglas que nunca llegaron a correr, y un valor no nulo
  suprime la declaración de no evaluable para todas.** CONFIRMADO sobre un corpus sintético
  (3 `clock.wait` + 1 `wiki.edit` dio `memory_governed_events: 3` y
  `non_evaluable_rules: []`, aunque `clock-budget` se evaluó cero veces porque las tres
  cayeron en args). Inalcanzable con el corpus de hoy; se rompe en cuanto llegue otro dataset,
  que es justo cuando P0-03 importa.
- **M6. La guardia de imports es más débil que la garantía que anuncia el README.** CONFIRMADO.
  `test_replay_never_executes` mira solo el AST del propio `replay.py`. El revisor probó
  `from bouncer.executor import run_script` + `importlib.import_module('bouncer.tools')`: la
  guardia **pasa**. Un import transitivo le da a `replay` una tabla `TOOLS` viva con todas las
  pruebas en verde. El README afirma más de lo que la prueba sostiene.
- **M7. `MemoryView(agent_id, 0, 0)` hace que la capa de memoria del recorrido sea
  estructuralmente incapaz de bloquear**, y el resumen declara una regla de actualización de
  estado que el recorrido no implementa: «state is updated after an allow and never after a
  block» describe un comportamiento que el recorrido tampoco tiene tras un `allow`. La
  conclusión publicada sobrevive, porque descansa en `memory_governed_events == 0`, que sí se
  mide. La frase, no.

## BAJO

- Una línea JSON malformada lanza `JSONDecodeError` pelado, sin `path:line`, mientras que el
  resto de validaciones de la misma función dan las dos cosas.
- `open("w")` sin `newline="\n"`: los registros no son byte a byte idénticos en Windows, y
  P0-07 dice «cualquier máquina». Mismo comportamiento preexistente en el ejecutor.
- `docs/results.md` da el denominador 13.661 pero no menciona las 930 filas excluidas ni
  enlaza `cleaning.json`. (El revisor verificó 13.661 filas, 13.661 `rev_id` distintos y 3.099
  agentes: sin doble conteo, y cuadra con `cleaning.json`.)
- El README mezcla denominadores en frases contiguas: «12 calls, no blocks» (total) y luego
  «11 calls, 1 block» (recuento de `ok`).
- Dos aserciones vacías en el fichero de aceptación: `assert "1" in blocked_row` la satisface
  el `11`, y `assert "12" in row` es una subcadena sobre la fila entera. No son debilitaciones
  —el fichero es nuevo— pero no cazarían un número equivocado.
- Ninguna prueba ejercita las 13.661 filas reales, así que los números históricos publicados
  no tienen regresión automática: `docs/results.md` es tan cierto como la última regeneración
  manual.

## Adherencia al plan

Cumplidos: una línea por evento en orden de fichero; las doce claves sin `body`, fijadas por
prueba; decisiones idénticas entre capas; la declaración de no evaluable con su razón;
registros byte a byte idénticos entre dos recorridos; el tiempo de comprobación confinado al
resumen; la página del ejecutor byte a byte idéntica tras el bloqueo; los dos bloques de la
tabla separados con sus denominadores; las cuatro filas del guion legítimo con la bloqueada
etiquetada y explícitamente **no** llamada tasa de falsos positivos; la frase obligatoria
sobre la capa 2 en el registro histórico; rondas contadas además de llamadas. Las interfaces
coinciden con el plan y `replay` no toca `gate.py`.

**Ninguna prueba de aceptación fue debilitada.** El único cambio a un fichero de pruebas
existente es el docstring de `test_scaffolding.py` y un import añadido.

**Error de empaquetado mío, no defecto del código:** el revisor marca la cobertura ≥ 80 %
como no verificable porque `pytest-cov` no está declarado en `pyproject.toml`. Es cierto que
no está declarado, pero el comando de la puerta es
`uv run --with pytest-cov pytest -q --cov=bouncer`, que lo instala al vuelo. **No le pasé el
bloque de comandos de `/verify` en el extracto del plan**, así que no podía saberlo. Medido:
99 % (`demo.py` 98 %, `replay.py` 97 %).

## Lo que el diff por sí solo no puede responder

1. Si `docs/results-summary.json` y `docs/results.md` versionados los produjo **este** código
   sobre el corpus actual. Son internamente consistentes y cuadran con `cleaning.json`, pero
   confirmarlo exige regenerarlos, lo que los sobreescribe.
2. Si «la primera llamada de cada agente es un `wiki.edit`» es una propiedad del corpus o de
   la preparación de la fase 1. Hoy las 13.661 filas son `wiki.edit`, así que la frase
   publicada es cierta; si la preparación **pudo** haber conservado un `clock.wait` es
   pregunta de fase 1, y decide cuánto importa M5.
3. Licencia y procedencia del corpus de la wiki: fuera del alcance de este diff, abierto para
   el entregable.
