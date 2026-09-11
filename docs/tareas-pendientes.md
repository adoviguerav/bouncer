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

### 2. Leer el informe de METR y Redwood

Todo lo que este repositorio dice sobre el tablón de mensajes sobre la caché de Artifactory viene de resúmenes de búsqueda, no del original. Está en [hallazgos-metr-redwood.md](hallazgos-metr-redwood.md) con ese aviso.

PDF: https://metr.org/hugging-face-incident-report-aug-2026.pdf

**Qué comprobar al leerlo:**

- Las cifras: ~1.200 agentes, ~70.000 mensajes, 700 en el ataque, 96 transcripciones falseadas (~7 %).
- Cómo se alcanzaba la caché exactamente: si pasaba por el proxy de egress como destino permitido, o si era interna y ni lo tocaba. Ahora mismo el diseño dice que probablemente lo segundo, y que en cualquier caso el control de destino no tenía nada que decir.
- Si el informe nombra algún control que habría cortado ese canal.
- Si menciona el incidente de la wiki o relación entre ambos.

Hace falta antes de citar cualquier cifra en la entrega.

## Decisión pendiente

**El parámetro de la capa 2.** La capa 2 bloquea por acumulación y necesita un número: cuántos destinos distintos puede tocar un agente antes de que corte.

El número sale de la forma del encargo y **nunca** de mirar el corpus. Si se elige mirando los datos, se está ajustando para ganar contra la misma evidencia que luego se presenta.

**Propuesta:** 1 destino distinto por ejecución. Un encargo para una tarea no implica tocar un segundo objetivo. A partir del segundo, bloquea.

Se fija y se comitea **antes** de mirar la distribución de ediciones por ID del corpus.

**Aviso:** en el escenario permisivo la capa 1 ya bloquea las escrituras por operación, así que la capa 2 puede no añadir ningún bloqueo. Eso es un resultado que se informa, no un fracaso.
