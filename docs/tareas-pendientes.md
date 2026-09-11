# Tareas pendientes

## Para Adolfo

Dos cosas que no se pueden hacer desde una sesión de Claude Code en remoto, porque el proxy de salida bloquea esos dominios. Comprobado el 11 de septiembre de 2026 por WebFetch, curl y git: 403 en el túnel.

### 1. Descargar los ejemplos de trabajo correcto

**Qué es y por qué hace falta.** La wiki son 13.661 ediciones y todas son del incidente. El dataset entero es comportamiento malo. Si solo probamos el portero contra eso, una regla que bloquee absolutamente todo acierta el 100 %, y un portero que bloquea todo es inútil porque también pararía a un agente haciendo su trabajo.

Hace falta la otra mitad: agentes trabajando bien, haciendo lo que les mandaron, para contar cuántos bloqueamos por error. Es el grupo de control. Sin él podemos decir «bloqueamos lo malo» pero no «y dejamos pasar lo bueno», que es lo que hace que lo primero signifique algo. Los documentos lo llaman «carga legítima».

**Qué tiene que cumplir para servirnos.** Cinco cosas, y la primera es la que descarta casi todo:

0. **Ser de un incidente real.** No un benchmark con riesgos inyectados. El track es respuesta a incidentes.
1. Llamadas a herramienta con sus argumentos.
2. Un identificador de sesión o de agente.
3. La tarea que se le encargó al agente.
4. Casos buenos y casos malos.

**Regla: coge el primero que las cumpla y deja de buscar.**

### Lo que hay en el mundo de incident response

El problema de fondo: los repositorios de incidentes de IA son **catálogos narrativos**, no registros de acciones. Describen qué pasó en prosa. Ninguno te da la secuencia de llamadas que hizo el agente. Por eso casi nada sirve como entrada de un portero.

**1. Documented AI Agent Incidents, de METR.** `metr.org/agent-incidents/`. 44 incidentes en los que un agente hizo algo claramente contrario a la intención del usuario, puntuados en dos ejes: **overreach**, cuánto se pasó del alcance previsto sabiéndolo, y **deception**, qué hizo por ocultarlo.

El eje de overreach es exactamente lo que decide nuestro portero. **Es el único de la lista que sigue abierto de verdad:** no pude abrirlo, el proxy bloquea metr.org, así que no sé si trae acciones o solo el relato. Si trae acciones, es el mejor con diferencia. **Esta es la comprobación que importa.**

**2. AI Incident Database (AIID).** 962 incidentes y 4.743 informes. Descargable en Excel semanal y en volcados JSON, CSV y MongoDB desde `incidentdatabase.ai/research/snapshots`.
Casi seguro que es catálogo narrativo más taxonomía, sin acciones. No pude abrirlo tampoco. Míralo por descarte, pero no esperes nada como entrada del portero. Como contexto del informe sí vale.

**3. RealHarm. Descartado, comprobado.** Sus campos son `context`, `language`, `source`, `taxonomy`, `label` y `conversation` con turnos de rol y contenido. Son conversaciones de chatbot, no llamadas a herramienta. Y los 68 casos «seguros» no son trabajo bueno independiente: son las mismas conversaciones inseguras reescritas con la respuesta corregida. No sirve ni como mitad mala ni como mitad buena.
`github.com/Giskard-AI/realharm`, arXiv 2504.10277.

**4. La wiki, que ya tenemos.** 13.661 acciones reales de agentes reales en un incidente real, con identidad y hora.
Le falta la tarea encargada (hay que declararla) y los casos buenos (no hay). Y las acciones son ediciones, no llamadas recuperadas: `wiki.edit` es una adaptación declarada.

### Lo importante

Hay que separar dos cosas que es fácil mezclar:

- **Catálogos de incidentes reales: haberlos, haylos.** AIID tiene 962, METR 44, RealHarm 136.
- **Datasets con las acciones del agente, llamadas y argumentos: no he encontrado ninguno** aparte de la wiki. Los 17.613 de Hugging Face son conteos por fase, no llamadas.

Los catálogos describen lo que pasó en prosa. Eso no se le puede dar de comer a un portero.

De los tres, RealHarm está comprobado que no trae acciones, AIID casi seguro que tampoco, y de los 44 de METR no lo sé porque no puedo abrirlo.

Si al comprobar METR se confirma, la conclusión es: **usamos la wiki, declaramos el encargo, y los casos buenos nos los montamos nosotros.** Y eso va en el informe como hallazgo, porque es un resultado en sí: en respuesta a incidentes de agentes no existe evidencia pública a nivel de llamada, y sin ella no se puede evaluar ningún control. Es justo lo que argumenta el observatorio de CLTR que cita el documento del sprint.

**Para la mitad buena, si hace falta:** AgentLogs, 549.239 sesiones reales del agente de GitHub con llamadas paso a paso, trabajo normal de programación. arXiv 2608.29204.

### 2. Leer el informe de METR y Redwood — opcional, no bloquea

Lo que el repo dice del 7 % de transcripciones falsificadas y del tablón sobre la caché
de Artifactory viene de cobertura de prensa, no del original. Está declarado así en
[hallazgos-metr-redwood.md](hallazgos-metr-redwood.md).

No hace falta para construir nada. Solo importa si en el informe final quieres afirmar
esas cifras como dato propio en vez de citar la cobertura. Si no, se cita lo que se ha
leído de verdad y listo.

PDF, por si acaso: https://metr.org/hugging-face-incident-report-aug-2026.pdf

### Cerrado: el descuadre de las ediciones

La cobertura pública habla de 14.666 ediciones; `revisions.jsonl.gz` tiene 14.591.
**Manda el fichero**: lo publicaron los autores, las sumas SHA-256 cuadran con su
manifiesto y el conteo está verificado. La diferencia se anota en una línea del informe
y no se investiga más.

## Cerrado: el parámetro de la capa 2

Ya no hay número que decidir. La versión anterior proponía un límite de destinos
distintos por agente; se retiró porque era una afirmación sobre comportamiento
disfrazada de regla de autorización, y circular además.

La capa 2 tiene ahora una regla que sale de la tarea y de un fallo documentado: la
tarea impone esperas obligatorias entre rondas, y los agentes usaron `clock.wait` para
saltárselas. Cada llamada vale; el abuso es el patrón. Ver
[hallazgos-tarea-wiki.md](hallazgos-tarea-wiki.md) §4.

Con el corpus de la wiki esa regla no se puede reproducir, porque solo hay ediciones y
no llamadas al reloj. Se demuestra en el programa de prueba local, en la fase 2.
