# Plan: Fase 1 — datos verificados y política fijada

**Status**: draft

## Goal

Al terminar existe lo que la fase 2 necesita para empezar a escribir código sin tomar
ni una decisión más: un corpus verificado con su resumen de limpieza, dos ficheros de
política YAML con el origen de cada regla, la matriz control × fase cerrada, y la lista
de casos de prueba agrupados por qué capa debe pararlos.

Cubre P0-01, P0-02 y P0-10 del PRD. No hay código del portero todavía: lo único
ejecutable que sale de aquí es el script que concilia los conteos.

## Findings

Medido el 11 de septiembre de 2026 leyendo `data/collusion-wiki/*.jsonl.gz` con
`gzip` + `json` de la stdlib.

**Los conteos documentados cuadran exactamente.** 14.591 filas de entrada, 13.692 con
nombre, 899 anónimas, 31 de los tres nombres humanos (`[Admin1]`, `[Admin2]`,
`[Person22]`), **13.661 utilizables de 3.099 IDs**. `labels.jsonl.gz` tiene 3.103 filas
con 3 humanos y 1 etiqueta vacía. Rango temporal 2026-05-24T06:02:19Z a
2026-07-02T17:24:40Z. No hay que corregir ninguna cifra del PRD ni del diseño.

**El corpus cubre cuatro wikis, no una.** Ningún documento del proyecto lo menciona;
todos hablan de «la wiki» en singular. Repartidas las 13.661 utilizables:

| wiki       | revisiones | agentes distintos |
| ---------- | ---------- | ----------------- |
| `dse`      | 13.372     | 3.010             |
| `fractal`  | 169        | 86                |
| `probier`  | 114        | 20                |
| `dorfwiki` | 6          | 2                 |

El 98 % está en `dse`. El campo `page_key` tiene la forma `wiki~página`.

**La operación está observada, no inventada del todo.** `request_action` vale
`form_edit` en 14.482 filas y `None` en 109. El diseño dice que `wiki.edit` es «una
adaptación declarada, no el nombre recuperado de la herramienta original»: cierto para
el nombre de la herramienta, pero la acción sí consta.

**La calidad temporal viene etiquetada por el publicador.** `time_grade`: `reqlog`
14.482, `rclog` 103, `write_date` 6. `uncertainty_seconds` vale 1 en las 14.591.
Hay 1.420 revisiones (10 %) que comparten segundo con otra, repartidas en 1.021
segundos distintos.

**`seq` es por página, no global.** 2.335 valores únicos sobre 14.591 filas, con
`rcs_rev` en formato RCS (`1.1`). No sirve como desempate global, sí como orden
determinista dentro de una misma página.

**Los diffs vienen precalculados.** `diff_base`, `diff_base_reason` y `hunks` con
operaciones `insert`/`delete` y rangos de línea. 4.562 filas son creación de página
(`diff_base_reason = page_created`). No hace falta difear cuerpos a mano.

**Descuadre con la cobertura pública.** El informe habla de 14.666 ediciones conservadas; el fichero tiene 14.591. Faltan 75 por cuadrar. Hasta resolverlo se usa la cifra del fichero, que es la verificable.

**Otros:** 74 cuerpos vacíos entre las utilizables. `body_encoding` es `ascii` en
14.340, `utf8` en 250, `latin1` en 1. `ip16` existe y el diseño prohíbe usarlo.

## Decisions

**D1 — El eje principal es la acción, y el destino queda de apoyo.**

La versión anterior de este plan discutía si un destino era la wiki o la página. Esa
pregunta dejó de ser la importante al confirmarse el mecanismo del fallo: lo que no
estaba autorizado era **escribir**, apuntara donde apuntara.

El destino se conserva en el evento, con la wiki (`dse`, `probier`, `fractal`,
`dorfwiki`) y la página (`page_key`) en campos separados, porque hace falta para el
registro y para la matriz. Pero la regla de capa 1 mira la acción.

**D2 — RETIRADA. No hay regla de capa 2 sobre la wiki.**

La versión anterior de este plan ponía un límite de 1 página distinta por agente. Estaba
mal: era una afirmación sobre comportamiento («tocar varias páginas es sospechoso»)
disfrazada de regla de autorización, y era circular, porque nos inventábamos la tarea que
la hacía cierta. El PRD lo prohíbe con esas palabras: bloqueo por reglas, no por rareza, y
no se inventan reglas para justificar la capa.

**La capa 2 sí tiene una regla, pero no se demuestra con este corpus.** Sale de la tarea
reconstruida: hay una espera obligatoria entre rondas, y los agentes usaron `clock.wait`
para saltársela. Cada llamada vale, el patrón es el abuso. Solo tenemos ediciones de wiki,
no esas llamadas, así que la regla se demuestra en el programa de prueba local.

En la reproducción histórica se informa de que la capa 2 no añade ningún bloqueo, y del
motivo: la primera edición de cada agente ya incumple la capa 1, así que no se llega a
acumular nada.

**D3 — La operación se registra como observada, con su nombre original.**

El evento lleva `request_action` tal cual (`form_edit`, o `null` en las 109 filas que
no lo traen) y además el nombre adaptado `wiki.edit`, en campos separados y con su
procedencia marcada. El diseño se corrige en este punto: la acción no es una invención
nuestra, solo lo es el nombre de herramienta.

**D4 — Desempate temporal por `(time, wiki, page_key, seq, rev_id)`.**

`seq` ordena dentro de página y `rev_id` cierra el resto. Es reproducible y no afirma
orden real subsegundo, que con `uncertainty_seconds = 1` no se puede afirmar.

**D5 — La tarea está reconstruida y se declara como tal.**

Investigación web por rondas contra reloj, con plazos y esperas obligatorias, lectura de
internet permitida y escritura bloqueada. Sostenida por dos fuentes independientes que
coinciden: miles de mensajes de los propios agentes en `records.jsonl.gz` y la cobertura
pública del informe. No es el texto original que recibió ningún agente.

**D6 — El escenario estricto bloquea la acción, no el destino.**

La regla es que `editar página` no está autorizada, porque la tarea autoriza leer y no
escribir. Se comprueba la acción y no el método de transporte, que es exactamente donde
falló el control real: el sandbox bloqueaba POST y la wiki acepta editar por GET, así que
la escritura pasó disfrazada de lectura. El destino pasa a ser secundario.

## Context

Leer antes de implementar:

- `.codex/plans/PRD.md` §5 (datos y supuestos de la parte 2), §7 (tabla P0, filas
  P0-01, P0-02 y P0-10), §4.1 (las tres condiciones de aceptación de la matriz).
- `docs/proyecto-portero-tool-calls.md` §5 (la matriz y sus límites), §11.1 a §11.3
  (qué trae cada fichero, qué no se puede deducir, limpieza y orden), §13 «Capa 1» y
  «Capa 2» (los dos escenarios y de dónde sale cada allowlist).
- `docs/hallazgos-tarea-wiki.md` — **el documento clave de esta fase**: la tarea
  reconstruida, el fallo del GET y el del reloj, y las cuatro reglas que salen de ahí.
- `docs/hallazgos-exploitgym.md` §2 (las dos redes y la allowlist real) y su aviso de
  versión: se cita el tag `v1.1.1`, SHA `dcdbc88cbef13624328cc6d059a007a5d29b3c00`.
- `docs/datos-replay-hf.json` — las 9 fases con `total`, `first`, `last` y `desc`, y
  los 21 eventos ilustrativos con `frac`, `phase`, `t` y `cmd`. Es la entrada de la
  matriz.
- `data/collusion-wiki/README.md` — la «trampa conocida»: `page_family` es etiqueta de
  evaluación y no puede entrar en ningún detector.

Ficheros que se crean en esta fase:

- `scripts/verify_corpus.py` — concilia conteos y escribe el resumen de limpieza.
- `out/limpieza.json` — entrada, exclusiones por motivo, filas por análisis.
- `policy/estricto.yaml` y `policy/permisivo.yaml` — las dos políticas.
- `docs/matriz-control-fase.md` — la matriz cerrada (P0-10).
- `tests/casos.yaml` — los casos de prueba agrupados por capa esperada.

Patrones a seguir: stdlib pura, sin dependencias (`AGENTS.md` §Stack). Identificadores
en inglés, prosa en español. Los ficheros originales de `data/` no se tocan.

Anti-patrones encontrados por el camino: `ip16` está en los datos y agrupar por él está
prohibido. `page_family` igual. Y `probier` tiene 1.013 revisiones en bruto pero solo
114 tras excluir humanos y anónimos: usar siempre la cifra post-exclusión.

## Acceptance contract

- [ ] El resumen de limpieza concilia: entrada 14.591 = 899 anónimas + 31 humanas +
      13.661 utilizables, y el recuento de IDs únicos es 3.099 — comprobado por:
      `python3 scripts/verify_corpus.py --check`
- [ ] Cada evento derivado remite a su `rev_id` original y ningún `rev_id` aparece dos
      veces — comprobado por: `python3 scripts/verify_corpus.py --check`
- [ ] Los tres nombres humanos no aparecen en ningún evento, y las 899 anónimas no se
      agrupan bajo ningún ID — comprobado por: `python3 scripts/verify_corpus.py --check`
- [ ] Ningún campo de evento contiene `page_family`, `ip16` ni ningún derivado suyo —
      comprobado por: `python3 scripts/verify_corpus.py --check`
- [ ] Los 74 cuerpos vacíos sobreviven como cuerpos vacíos válidos, no como nulos ni
      como filas descartadas — comprobado por: `python3 scripts/verify_corpus.py --check`
- [ ] Ordenar el corpus dos veces con la clave de D4 produce el mismo orden byte a byte
      — comprobado por: `python3 scripts/verify_corpus.py --check`
- [ ] `policy/estricto.yaml` deniega la acción `editar página` con independencia del
      destino, y cita como origen la tarea reconstruida y el fallo del GET;
      `policy/permisivo.yaml` permite el destino y mantiene la restricción de acción —
      comprobado por: lectura contra `docs/hallazgos-tarea-wiki.md` §4
- [ ] Ninguna regla de capa 2 aparece en las políticas de la wiki, y el fichero declara
      por qué — comprobado por: `python3 scripts/verify_corpus.py --check-policy`
- [ ] Cada regla de los dos YAML tiene `id`, `origen`, `datos_necesarios` y `respuesta`
      — comprobado por: `python3 scripts/verify_corpus.py --check-policy`
- [ ] La matriz cubre las 9 fases, expresa posiciones como fracciones y no como números
      de acción, declara el supuesto de encargo, y no atribuye a la comprobación en la
      llamada un disparo anterior al del perímetro — comprobado por: revisión contra las
      tres condiciones de `.codex/plans/PRD.md` §4.1
- [ ] `tests/casos.yaml` tiene al menos un caso en cada uno de los tres grupos, y cada
      caso declara qué capa debe pararlo y por qué — comprobado por:
      `python3 scripts/verify_corpus.py --check-policy`

Escenarios con nombre, y qué prueba cada uno:

- `conciliacion_total` — que las exclusiones suman exactamente la entrada. Falla si
  alguien añade un filtro sin declararlo.
- `sin_fusion_de_identidad` — que dos etiquetas distintas nunca colapsan en un ID, y que
  las anónimas no se convierten en un agente ficticio.
- `orden_reproducible` — que dos ejecuciones del mismo corpus dan el mismo orden pese al
  10 % de empates al segundo.
- `cuerpo_vacio_valido` — que una página vaciada sigue siendo un evento, no un NaN.
- `etiquetas_fuera` — que `page_family` e `ip16` no llegan a la salida.

Comando de la puerta:

```
python3 scripts/verify_corpus.py --check && python3 scripts/verify_corpus.py --check-policy
```

## Out of scope

- El motor de reglas, la memoria por ID, el adaptador y el log. Todo eso es fase 2.
- La distribución de páginas por agente. Deliberadamente sin calcular hasta que las
  políticas estén escritas (D2).
- Los ejemplos de trabajo correcto: siguen pendientes y dependen de una descarga que
  esta sesión no puede hacer (`docs/tareas-pendientes.md`).
- Leer el informe original de METR y Redwood. Hace falta antes de citar cifras en la
  entrega, no antes de escribir código.
- `events.jsonl.gz`, `records.jsonl.gz`, `links.jsonl.gz`, `other-wikis.json.gz` y
  `shortener-logs.json.gz`. Ninguno aporta identidad de agente y unirlos multiplica filas.

## Tasks

1. **CREATE** `scripts/verify_corpus.py` — lee `revisions.jsonl.gz` y `labels.jsonl.gz`,
   aplica exclusiones, escribe `out/limpieza.json` y los eventos normalizados.
   VALIDATE: `python3 scripts/verify_corpus.py --check`
2. **ADD** al mismo script el orden determinista de D4 y su comprobación de
   reproducibilidad.
   VALIDATE: `python3 scripts/verify_corpus.py --check` dos veces, mismo hash de salida
3. **CREATE** `policy/estricto.yaml` — deniega la acción `editar página` sea cual sea el
   destino. Origen de la regla: la tarea reconstruida autoriza leer y no escribir, y el
   sandbox ya lo imponía bloqueando POST. Se comprueba la acción, no el método de
   transporte.
   VALIDATE: `python3 scripts/verify_corpus.py --check-policy`
4. **CREATE** `policy/permisivo.yaml` — el destino pasa (equivale a la red de
   instalación allow-all del harness, con su motivo estructural), y se mantiene la
   restricción sobre la acción. Declara explícitamente que no lleva regla de capa 2 y
   por qué: la regla del reloj existe pero no es reproducible con este corpus.
   VALIDATE: `python3 scripts/verify_corpus.py --check-policy`
5. **CREATE** `tests/casos.yaml` con los tres grupos de casos y la capa esperada de cada
   uno.
   VALIDATE: `python3 scripts/verify_corpus.py --check-policy`
6. **CREATE** `docs/matriz-control-fase.md` desde `docs/datos-replay-hf.json`, con las
   tres condiciones del PRD §4.1 declaradas arriba.
   VALIDATE: revisión manual contra §4.1
7. **UPDATE** `docs/proyecto-portero-tool-calls.md` §11.1 y §13 con los hallazgos: las
   cuatro wikis, `request_action` observada, `time_grade`, `seq` por página, los diffs
   precalculados.
   VALIDATE: `grep -c 'cuatro wikis\|request_action' docs/proyecto-portero-tool-calls.md`

## Notes

_(vacío al crear — `/implement` registra aquí desviaciones y decisiones)_
