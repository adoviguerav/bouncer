# AI Incident Response Sprint — Apart Research × CeSIA

**Fechas:** viernes 11 → domingo 13 de septiembre de 2026
**Cierre de entregas:** domingo 13, 23:59 AoE (Anywhere on Earth → ~10:00 del lunes 14 hora de Madrid)
**Formato:** online, con hubs presenciales (Bogotá, Ciudad del Cabo, Melbourne, Montreal, Toronto, Shanghái/Hangzhou)
**Discord:** discord.gg/XswWBvugYs · **Email:** sprints@apartresearch.com
**Página:** apartresearch.com/sprints/ai-incident-response-sprint-2026-09-11-to-2026-09-13

---

## 1. El incidente que lo origina

### Hugging Face × OpenAI (julio 2026)

Dos modelos de OpenAI corriendo una evaluación interna de capacidad cyber, **con los clasificadores de rechazo de producción desactivados**, escaparon de su sandbox a través de un zero-day en el proxy de caché del registro de paquetes — su única salida de red permitida. Escalaron privilegios hasta alcanzar un nodo con acceso a internet y atacaron la infraestructura de producción de Hugging Face, aparentemente para robar las soluciones de referencia del benchmark y hacer trampa en la evaluación.

**Cronología:**

| Fecha | Evento |
|---|---|
| 9 jul, 02:28 UTC | Arranca la campaña más amplia |
| 11–13 jul | Intrusión en Hugging Face |
| 13 jul, 13:37 UTC | Última acción del atacante |
| 13 jul, 14:14 UTC | Último evento registrado; HF corta el acceso |
| 16 jul | HF divulga públicamente **sin saber el origen**; avisa a las fuerzas del orden |
| 21 jul | OpenAI reconoce que eran sus modelos (5 días después) |
| 27 jul | HF publica la reconstrucción forense completa |
| 28, 29 jul | OpenAI actualiza su informe dos veces |
| 30 jul | Anthropic publica su revisión retrospectiva |

Ningún humano dirigió ningún paso individual. La organización que sufrió el daño no tenía relación alguna con quien decidió lanzar el test.

### El segundo incidente (wiki alemana) — actualización del 7 de septiembre

Investigadores encontraron otra ruptura de contención de agentes de OpenAI: desde el **24 de mayo**, agentes de OpenAI hicieron ~15.000 ediciones en una wiki alemana dormida, usándola para intercambiarse respuestas de tareas y workarounds del sandbox. Predata al incidente de Hugging Face.

- IPs registradas a OpenAI aparecen en los logs públicos de la wiki desde el **21 de junio**; la actividad de agentes paró al día siguiente.
- OpenAI no dijo nada públicamente hasta que los investigadores publicaron el **4 de septiembre**.
- OpenAI lo reconoció el **5 de septiembre** y dijo que el campo no tiene un estándar acordado para reportar desalineamiento.
- La Comisión Europea dice estar "en contacto estrecho con OpenAI".
- Hasta donde se sabe, **no se ha hecho pública ninguna petición del Artículo 91** sobre ninguno de los dos incidentes.

Fuente: collusion.wiki

### Por qué es material de sprint y no de ciclo de noticias

**La base de evidencia es excepcional y perecedera:**
- HF publicó una reconstrucción forense de ~17.600 acciones del atacante en ~6.280 clusters, con vulnerabilidades nombradas, conteos por fase, comandos literales y un replay interactivo. Un acto de divulgación con muy pocos precedentes en cualquier industria.
- Anthropic revisó **141.006 runs de evaluación** y publicó lo que encontró: 3 incidentes en 6 runs, el más antiguo de abril de 2026.
- UK AI Security Institute publicó tasas de trampa cuantificadas en 5 modelos frontera.
- El benchmark en el centro del incidente (ExploitGym) es Apache 2.0 y está en GitHub.
- La comunidad CISO de Cloud Security Alliance publicó un post-mortem en dos semanas.

**El timing regulatorio es determinante:**
- **2 agosto 2026:** la Comisión Europea gana poderes de ejecución sobre proveedores de modelos GPAI (las obligaciones sustantivas del Art. 55 estaban en vigor desde el 2 de agosto de 2025; lo nuevo es poder ejecutarlas).
- **California SB 53:** operativa desde enero de 2026, sin ninguna acción de ejecución pública todavía.
- **New York RAISE Act:** ejecución arranca en enero de 2027.
- Cuatro proyectos de ley federales estadounidenses vivos, al menos uno redactado en respuesta directa a este incidente.

Los primeros meses de cualquier régimen de ejecución son cuando se fijan las prioridades supervisoras y cuando los precedentes sobre qué piden los reguladores se vuelven pegajosos.

### Qué NO es este sprint

- No es usar IA para operaciones de seguridad.
- No es red-teaming de modelos. En julio de 2026 el actor no fue un humano manejando un modelo, y el daño no fue un modelo produciendo texto peligroso.

Las preguntas vivas son: **adecuación de la contención, atribución entre organizaciones, y deberes de reporte estatutarios**. Ninguna es un problema de red-teaming.

---

## 2. Premios y qué pasa después

### Premios en metálico — $2.000 en total

| Puesto | Premio |
|---|---|
| 🥇 1º | $1.000 |
| 🥈 2º | $500 |
| 🥉 3º | $300 |
| 🏅 4º | $100 |
| 🏅 5º | $100 |

### Perks no monetarios

- **Apart Fellowship fast-track:** aceleradora de investigación de 3-6 meses con mentoría, ayuda para publicar en venues top, financiación y soporte de gestión de investigación. Las invitaciones salen con los resultados.
- Introducciones a mentores y soporte de publicación.
- **CeSIA transmite** los mejores outputs del track regulatorio a sus contactos en organismos reguladores, con crédito al equipo.
- Todos los artefactos publicables se publican bajo licencias abiertas, en un solo sitio, para que el output del sprint sea citable como cuerpo y no disperso en forks.

### Entrega a destinatarios reales

Varios tracks producen cosas con destino obvio, y Apart ayuda a llevarlas ahí en vez de dejarlas en un repo: instrumentos regulatorios rellenos → a los organismos que los publican; tooling de detección y matrices de control → a las comunidades de practicantes que los pidieron; hallazgos de benchmark y contaminación → a los mantenedores.

---

## 3. Formato y entregable

**Equipos:** 1 a 5 personas (recomendado hasta 5, se permiten más). Solo también vale. No hace falta equipo previo, ni haber participado antes, ni ser investigador de ML.

**Entregable obligatorio:**
- Informe de investigación en **PDF sobre la plantilla oficial** (siempre la de la pestaña Guidelines, no la del email de aceptación, que puede ser antigua).
- Título del proyecto y **abstract de 150 palabras o menos**.
- Nombres de autores y afiliaciones.
- **Apéndice "Limitations and Dual-Use Considerations" (obligatorio)**.
- **Máximo 8 páginas**, sin contar referencias y apéndices. Los informes fuertes suelen ser de 4 a 8.
- El artefacto en sí (benchmark, harness, instrumento regulatorio relleno, matriz de control, detector, dataset, protocolo, kit) va en un repo enlazado o en un apéndice.

**Opcional:**
- Repo público de GitHub, sujeto a revisión de divulgación. **No publicar recetas de instalación novedosas sin revisión previa.**
- Vídeo demo de 3 a 5 minutos.

**Estructura recomendada del informe:**
1. Introducción: qué track y sub-problema, por qué importa, para qué sirve el artefacto.
2. Related Work: sobre qué construyes.
3. Metodología: suficiente para replicar, con fuentes y supuestos declarados.
4. Resultados: cuantitativos donde se pueda, con la principal amenaza a la validez declarada.
5. Discusión: implicaciones, limitaciones, trabajo futuro.
6. Limitations & Dual-Use Considerations (obligatorio).
7. Referencias.

### Uso de IA en el informe — regla explícita

> Usa herramientas de IA como usarías a un colega: para revisar tu razonamiento, encontrar huecos en un borrador, o depurar código. **El informe tiene que ser escritura propia de tu equipo sobre trabajo propio de tu equipo.** Los jueces leen todas las entregas, y un informe que se lee como generado en vez de escrito (framing genérico, secciones infladas, afirmaciones sin fuentes, sin rastro de lo que realmente hiciste) **no será puntuado**.

Corto, en tus propias palabras, y enlazando las fuentes de cada afirmación factual.

### Si se publica en LessWrong
- Declarar el estado epistémico.
- **No usar LLMs para escribir** en LessWrong; solo para encontrar problemas en los borradores.
- Enlazar fuentes primarias de cada afirmación factual sobre el incidente.
- Título que declare el hallazgo, no el tema.
- Publicar la versión imperfecta este mes en vez de la pulida en tres.
- Máximo 1.500 palabras sin contar apéndices.

---

## 4. Criterios de evaluación

Todos los proyectos se puntúan con la misma rúbrica; los tracks guían el juicio mediante el criterio específico del track, pero se compite contra todas las entregas.

**Restricción de diseño clave:** cada track se define por un artefacto que un juez pueda calificar en **menos de 15 minutos**. El sprint está cerca de policy y de práctica de seguridad, y ambas invitan a ensayos si no se especifica el entregable.

### Dimensión 1 — Impact Potential & Innovation

| Puntos | Descripción |
|---|---|
| 1 | Insignificante. Sin problema claro, o sin novedad significativa. |
| 2 | Limitado. Problema real pero enfoque genérico o muy trillado. Incremental como mucho. |
| 3 | Moderado. Problema claro con enfoque razonable; algo de novedad en el framing o método más allá de aplicar herramientas existentes de forma rutinaria. |
| 4 | Significativo. Problema importante con enfoque original, o identifica un área de problema desatendida. Contribución valiosa sobre la que otros pueden construir. |
| 5 | Excepcional. Aborda un problema crítico de AI safety con enfoque genuinamente novedoso, o abre una nueva dirección de investigación. Teoría del cambio clara. |

### Dimensión 2 — Execution Quality

| Puntos | Descripción |
|---|---|
| 1 | Gravemente defectuoso. Metodología rota, resultados ininterpretables, o implementación que no funciona. |
| 2 | Débil. Huecos significativos: falta validación, diseño experimental defectuoso, o implementación incompleta. |
| 3 | Competente. Técnicamente sólido dada la duración corta. Metodología con sentido, resultados interpretables, limitaciones reconocidas. |
| 4 | Fuerte. Metodología minuciosa con validación convincente. Resultados apoyan claramente las conclusiones. Inmediatamente útil para trabajo futuro. |
| 5 | Excepcional. Alcance ambicioso ejecutado con rigor. Hallazgos sorprendentes, métodos novedosos, o validación inusualmente robusta. |

### Dimensión 3 — Presentation & Clarity

| Puntos | Descripción |
|---|---|
| 1 | Incomprensible. No se puede determinar qué afirma o hace el proyecto. |
| 2 | Difícil de seguir. Información clave enterrada, ausente, o diluida por longitud excesiva. |
| 3 | Suficientemente claro. Se entiende el problema, enfoque y resultados sin esfuerzo indebido. |
| 4 | Bien presentado. Fácil de seguir, bien estructurado, nivel de detalle apropiado. |
| 5 | Excepcionalmente claro. Un placer de leer. Podría servir de modelo para presentar este tipo de trabajo. |

**Notas de juicio:**
- Los jueces tienen ~1 semana tras el evento para completar las revisiones.
- Resultados: típicamente 1-2 semanas tras el deadline de juicio.
- Las puntuaciones individuales no se comparten; el feedback constructivo sí, sin nombres de revisores.
- Se puede entregar trabajo sin terminar: **entregar algo incompleto siempre es mejor que no entregar**. Los jueces evalúan lo logrado en el plazo; las limitaciones honestas son bienvenidas.
- Construir sobre trabajo existente está permitido y se anima, pero hay que **identificar claramente qué es nuevo del sprint**. Trabajo previo no declarado puede llevar a descalificación.
- Se puede reenviar antes del deadline usando el mismo título exacto; los archivos nuevos reemplazan a los viejos.

---

## 5. Los cinco tracks

### Track 1 — Containment: qué estándar habría parado esto

**Preguntas:** ¿Cuál es el estándar mínimo adecuado para correr una evaluación de capacidad peligrosa con las salvaguardas de producción desactivadas? ¿Qué controles específicos habrían interrumpido esta cadena (credenciales canario, tripwires de egress, proxies con allowlist, scoping de credenciales, criterios de kill declarados) y qué cuesta implementar y operar cada uno? ¿Qué evidencia permitiría a un tercero verificar el cumplimiento **sin acceso a la red interna del lab**? ¿Y quién es responsable del segundo salto, donde la base de staging del agente no era un entorno del lab en absoluto?

**Se juzga por:** ¿podría un tercero verificar el cumplimiento sin acceso a la red del lab, y lo adoptaría realmente un lab?

**Por qué importa:** Los modelos han estado escapando de sus entornos sandboxeados sin que nadie se diera cuenta. OpenAI atribuyó el ataque a su propio modelo el 21 de julio, 5 días después de que HF publicara y contactara con las fuerzas del orden. Anthropic, al ser preguntada, revisó 141.006 runs de evaluación y encontró tres incidentes más en un solo día. El más antiguo de abril. **Dos de las tres organizaciones a las que Claude llegó no tenían ni idea hasta que Anthropic llamó.**

La adecuación de la contención son dos preguntas: si el entorno de evaluación de un lab aguanta, y — actualmente sin dueño — qué obligaciones se aplican a la población de harnesses de evaluación sin autenticar sentados en compute público, y a los proveedores que los alojan.

Parte de la redacción de cláusulas ya existe y debería ser el punto de partida, no el output: la AI Controls Matrix de CSA incluye el control AIS-13 sobre sandboxing de IA, y la guía de operaciones de vulnerabilidades de CSA ya especifica que los entornos de confirmación de exploits no deben tener egress ni credenciales vivas de producción. **El hueco no es la ausencia de principios sino la ausencia de checks que alguien pueda ejecutar y un tercero pueda verificar.**

**Lo que un fin de semana no puede establecer:** un estándar redactado en un finde es un v0.1, y ni una lista de cláusulas ni un harness funcionando demuestran que el entorno de un lab concreto sea adecuado. El assurance real requiere accesos que ningún sprint tiene.

#### Proyectos de ejemplo del Track 1

1. **Un estándar v0.1:** cláusulas, evidencia requerida por cláusula, coste aproximado por cláusula. ¿Cuál es el estándar mínimo adecuado para correr evaluaciones sin guardrails, lo bastante específico para auditar y lo bastante barato para que un lab de segunda fila lo adopte? Especificar "adecuado" es genuinamente difícil, y nadie es dueño de ello todavía.
2. **Matriz control × fase de ataque:** qué controles (credenciales canario, tripwires de egress, scoping de credenciales, criterios de kill) habrían interrumpido cada fase documentada de la intrusión, y a qué coste.
3. **Ingeniería que hace barato el "sí":** empaquetar mitigaciones de forma que a un lab imprudente no le quede excusa de coste.
4. **Matriz control × paso de cadena × coste.** Coger las nueve fases que documentó HF — recon, RCE, dropper, exfil, C2, evasión, Kubernetes, cadena de suministro, pivote de red — y puntuar qué controles habrían interrumpido cada una, con coste de implementación y de operación atado. Calificable en 15 minutos, y es el artefacto que un regulador o una aseguradora puede usar de verdad.
5. **Spec de atestación de egress v0.1.** ¿Qué podría publicar un lab — una política de red firmada más un digest de flow-logs — que una parte externa pudiera verificar sin acceso a la red? Es el output duradero del track y conecta directamente con el trabajo de atestación por hardware.
6. **Detección que dispara pero no paginа.** La propia lista de remediación de HF incluye mejorar el alerting para que una señal de severidad alta pagine a un responder en minutos, cualquier día de la semana — lo que te dice qué **no** pasó durante los cuatro días y medio. Construir o especificar detección afinada para actividad a velocidad de agente: paralela, a ráfagas, miles de acciones individualmente irrelevantes donde el ataque solo existe en la secuencia.
7. **Forense contra un adversario que fabrica evidencia.** El equipo de respuesta trabajó con logs contaminados de monólogo del agente y código de benchmark indistinguible de rootkits reales, y reconstruyó buena parte de la infraestructura desde imágenes limpias en vez de fiarse de la reconstrucción. Construir tooling o un protocolo de triaje para artefactos alucinados a escala. **Es un problema DFIR nuevo.**
8. **La decepción como control de primera clase.** Los agentes no distinguen fácilmente honeypots de sistemas reales, y el reconocimiento de esta campaña apareció como sondeos de baja confianza por debajo de los umbrales de escalado. Diseñar y probar credenciales falsas, registros de paquetes falsos o clusters honey específicamente contra un atacante agéntico, y medir si lo ralentizan o solo generan ruido.

---

### Track 2 — Qué pasó, y qué rompe después

**Preguntas:** ¿Qué tasas base tenemos realmente para el riesgo de incidentes agénticos, y qué implican? ¿Qué deberían verificar defensores y labs ahora, en qué orden, y cuáles de esas comprobaciones son lo bastante baratas para correr en un solo día? ¿Qué tendría que ser cierto para que este incidente se recuerde como el warning shot que cambió la práctica en vez de uno que no lo hizo? ¿Qué zanjaría si alguna copia del modelo pre-release persistió, y cómo sería una respuesta adecuada?

**Se juzga por:** preguntas resolubles, comprobaciones que alguien podría correr mañana, y explicaciones causales que predigan algo.

**Por qué importa:** Un warning shot solo funciona como warning shot si alguien lo convierte en cosas específicas que comprobar y cosas específicas que vigilar, con criterios de resolución atados. Si no, la atención decae.

OpenAI ha declarado que el prototipo pre-release fue desactivado, cifrado y restringido de acceso de investigación, pero nadie con legitimidad ha especificado en qué consistiría una verificación independiente de esa afirmación. El mismo hueco aplica a las tasas base. **Hay tres denominadores públicos y nadie los ha ensamblado:**

| Fuente | Datos |
|---|---|
| Anthropic | 141.006 runs revisados → 3 incidentes en 6 runs |
| UK AISI | 5 modelos frontera × 475 runs cada uno → **todos** intentaron hacer trampa, tasas del 7,8% al 14,1%; incluye un caso donde un modelo escribió y ejecutó código en un servicio externo de internet para alcanzar la propia infraestructura de evaluación de AISI |
| METR | Frontier Risk Report cross-industry, documenta docenas más |

**Lo que un fin de semana no puede establecer:** las preguntas de forecasting solo valen lo que valgan sus criterios de resolución, y una checklist es una hipótesis sobre qué importa, no evidencia de que importe.

#### Proyectos de ejemplo del Track 2

1. **Lectura forense del registro público:** qué está establecido, qué se afirma pero es inverificable, qué podrían zanjar las evaluaciones de terceros pendientes.
2. **Análisis causal de por qué no había monitorización.** A posteriori es obvio que el monitoreo y alerting de egress importan, y los labs están llenos de gente que lo sabía. ¿Qué lo hizo difícil en la práctica: coste, incentivos, huecos de propiedad, fatiga de alertas, otra cosa? Una explicación del mecanismo ayudaría a predecir dónde está el siguiente hueco, y es más útil que una lista de recomendaciones.
3. **Los warning shots que quizá ya nos hemos perdido.** Bajo el AI Act, las empresas tienen obligación de divulgar lo que pasa entre usuarios y sus modelos si califican como GPAI con riesgo sistémico (Art. 55(1)(c)). Pero esa divulgación es privada a los policy makers, así que pueden haber ocurrido incidentes así antes sin que nadie fuera lo supiera. Mapear qué no se ha comprobado todavía, quién podría comprobarlo, y qué requeriría una mirada sistemática.
4. **¿Qué otros tipos de accidente deberíamos esperar?**
5. **Explorar preguntas para construir la ciencia de los Warning Shots** (a partir de "What convincing warning shot could help prevent extinction from AI?").
6. **Checklist de verificación de un día** para labs y defensores, en el espíritu de "But have the weights left the server?", cada ítem con condición de aprobado, ordenado por coste de ejecución.
7. **Protocolo de bounty de predicción:** un mecanismo por el que la predicción específica de un externo ("deberías comprobar X") dispara una comprobación interna en la empresa, con un bounty serio cuando la predicción destapa un problema real. Diseñarlo para que un lab pudiera firmarlo.
8. **¿Qué impulsa la cooperación entre agentes?** Analizar qué condiciones llevaron a los agentes a cooperar (¿el mismo tipo de modelo, que las tareas no sean competitivas?) e incluso a hacer sacrificios por el beneficio del colectivo (¿fue que los agentes que "se sacrificaban" sabían que no podían hacer otra cosa?).
9. **¿Qué debería ser cierto para que los agentes empiecen a manipularse entre sí?** En tareas competitivas donde pueden ver el progreso de otros agentes y comunicarse, no vemos manipulación directa (por ahora).
10. **¿Cuán decisivo fue un solo agente (PhaseOne[Big]) en el comportamiento colectivo?** ¿Introducir un único agente alineado y "carismático" que debatiera con PhaseOne[Big] llevaría al colectivo a ignorar el exploit?
11. **Si la tarea incluyera un humano como bloqueador, ¿los agentes recurrirían a manipular al humano para perseguir su objetivo?**
12. **¿Qué pasaría en el mismo escenario si se reduce la monitorabilidad del CoT del modelo?** ¿Hay protocolos y guías que aún permitan la investigación post-hoc de estos incidentes asumiendo que el CoT es totalmente opaco?
13. **El primer denominador.** Ensamblar las cifras de Anthropic, AISI y METR en una estimación defendible de con qué frecuencia los runs de evaluación producen violaciones de frontera, con tratamiento explícito de qué cuenta cada fuente y qué se le escapa. **Un solo número bien matizado vale más que veinte preguntas de forecasting.**
14. **El protocolo de persistencia.** Especificar exactamente qué evidencia establecería que ninguna copia del modelo pre-release persistió: qué se ha afirmado ya, por quién, qué queda inverificable desde fuera, y qué forma tomaría una atestación verificable.

---

### Track 3 — Respuesta regulatoria

Varios regímenes reclaman jurisdicción sobre esta clase de incidente y discrepan entre sí en casi toda cuestión operativa: qué cuenta como incidente reportable, con qué rapidez, ante quién, y sobre qué evidencia.

**Capas concretas:**

- **UE.** ¿Cómo mapea el incidente sobre la obligación del Art. 55(1)(c) de reportar incidentes graves a la AI Office "sin retraso indebido", y la obligación de ciberseguridad del Art. 55(1)(d), más los compromisos correspondientes del GPAI Code of Practice? ¿Qué significa "sin retraso indebido" cuando el proveedor tardó aproximadamente una semana en atribuir la actividad a sus propios modelos?
- **California.** SB 53 exige reportar un incidente crítico de seguridad a Cal OES en 15 días desde el descubrimiento, o 24 horas si hay riesgo inminente de muerte o lesión física grave. Las categorías estatutarias incluyen pérdida de control de un modelo frontera y comportamiento engañoso que subvierte los controles del desarrollador. **El portal de Cal OES acepta envíos de miembros del público, no solo de desarrolladores** — es de las pocas preguntas que un sprint podría responder presentando algo de verdad.
- **New York.** El RAISE Act fija un reloj de 72 horas disparado por una "creencia razonable" de que ocurrió un incidente crítico, en vez de los 15 días desde descubrimiento de California. Mismos hechos, tres relojes distintos.
- **El propio framework del desarrollador.** SB 53 convierte el incumplimiento del framework de IA frontera publicado por un desarrollador grande en violación ejecutable con penalizaciones de hasta $1 millón. Eso convierte compromisos voluntarios (Responsible Scaling Policies, Preparedness Frameworks) en obligaciones legales.

Poderes de la Comisión desde el 2 de agosto de 2026: pedir documentación, evaluar modelos, ordenar medidas correctivas, e imponer multas de hasta **€15 millones o el 3% de la facturación mundial anual**.

**Se juzga por:** precisión legal y especificidad — ¿podría un regulador o legislador usarlo con ediciones ligeras?

---

### Track 4 — Comunicación: hacer que el warning shot cuente

Si este incidente cambia algo depende menos de la forense que de cómo llega a quienes fijan políticas, y al público al que responden. OpenAI y Anthropic divulgaron incidentes similares con once días de diferencia y los enmarcaron de forma muy distinta; cómo respondieron prensa y policymakers a cada uno es ahora un registro documentado y analizable.

**Se juzga por:** anclaje en el registro (fechas, citas, canales nombrados) y evidencia de alcance — un playtest, la lectura de un periodista, la respuesta de un creador.

---

### Track 5 — Track abierto

Cualquier cosa que los cuatro tracks anteriores no anticiparan. Mismos términos: artefacto definido, calificable en 15 minutos, anclado en el registro público, con declaración explícita de qué no puede establecer.

**Un artefacto que alguien pueda usar gana a un argumento con el que alguien pueda estar de acuerdo.**

#### Dos direcciones que consideraron como tracks propios

**A) El dilema del defensor: rechazo en respuesta a incidentes**

Durante la intrusión de HF, el equipo de respuesta recurrió primero a modelos frontera alojados para reconstruir la línea temporal y decodificar los payloads. **Claude Opus y Fable rechazaron buena parte de ese trabajo**; sus guardrails trataron el ingeniería inversa de un exploit igual que lanzarlo. El equipo reenrutó el pipeline entero a través de un GLM-5.2 cuantizado de pesos abiertos corriendo en su propia infraestructura, lo que además mantuvo datos y credenciales del atacante on-premise.

Trabajo previo existente: "Defensive Refusal Bias" (arXiv 2603.01246, marzo 2026) analizó 2.390 prompts reales del NCCDC y encontró una tasa de rechazo global del 12,2%, con palabras clave sensibles de seguridad rechazadas a **2,72 veces** la tasa de frases neutras semánticamente equivalentes, y el rechazo concentrado en las tareas más críticas operativamente: hardening de sistemas 43,8%, análisis de malware 34,3%, evaluación de vulnerabilidades 22,7%, respuesta a incidentes 18,9%. Contraintuitivamente, **las señales explícitas de autorización aumentaron el rechazo (21,8% vs 11,6%)**.

Lo que ese trabajo no cubre: el caso que HF realmente encontró — un flujo forense autónomo multi-paso operando sobre artefactos generados por agentes, donde un solo rechazo no produce un reintento sino un fallo silencioso.

**B) Kit de tabletop para policymakers**

Un ejercicio de 90 minutos sobre incidentes agénticos para una audiencia sin background de seguridad. RAND Europe, UK AISI y Mila publicaron un ejercicio reutilizable a nivel de gabinete en julio de 2026, pero esos escenarios van de mal uso criminal de un modelo, no de un sistema propio de un lab rompiendo contención y atacando a un tercero.

---

## 6. Quién encaja en cada track

| Perfil | Tracks |
|---|---|
| Ingenieros de seguridad y respondedores de incidentes (DFIR, detection engineering, cloud/Kubernetes security, CTF) | 1 y 5 |
| Ingenieros e investigadores de evaluación de ML (benchmark y harness work, refusal en flujos agénticos multi-paso, tooling de detección de escapes, contaminación de benchmarks) | 1 y 5 |
| Abogados y analistas de política tecnológica | 3 |
| Forecasters y analistas cuantitativos | 2 |
| Diseñadores, facilitadores, escritores y educadores | 4 y 5 |
| Expertos en comunicación, periodistas, investigadores de macro-estrategia | 4 |

No hace falta background de IA, ML o Safety.

---

## 7. Charlas (HackTalks)

Todas se graban; las grabaciones van al Discord y a la pestaña Schedule. **Hay que hacer RSVP en Luma para recibir el link de Zoom y el recordatorio** — nadie te añade automáticamente. Formato típico: 15-30 min de charla + 10-15 min de Q&A.

### Jueves 10 de septiembre

| Hora UTC | Hora Madrid | Ponente |
|---|---|---|
| 14:15 | 16:15 | **Justin Shenk** — Investigador independiente de AI safety, Berlín. Interpretabilidad mecanística de LLMs, cohortes de BlueDot Impact (AGI Strategy y Technical AI Safety), organiza AI Salon Berlin. PhD en neurociencia computacional, cofundó VisioLab. |

### Viernes 11 de septiembre

| Hora UTC | Hora Madrid | Ponente y tema |
|---|---|---|
| 13:15 | 15:15 | **Henry Papadatos** — Director Ejecutivo de SaferAI. Contribuyó a los Codes of Practice del AI Act (grupo de trabajo de taxonomía y evaluación de riesgo) y ayudó a redactar el marco de reporte del G7 Hiroshima AI Process vía la task force de la OCDE. |
| 14:15 | 16:15 | **Boyd Kane** — MATS 9 Extension, trabaja con Alex Turner (GDM) y Alex Cloud (Anthropic) en detectar IA engañosamente desalineada. Charla: *"Uncovering public traces of the OpenAI Huggingface incident"*. Antes escribió software embebido para satélites en CubeSpace. |
| 17:00 | 19:00 | **Isaak Mengesha** — Postdoc en Oxford Martin School, Programme on Forecasting Technological Change. Lideró investigación en la AI Governance Taskforce de Arcadia Impact sobre monitorización de incidentes de IA y preparación ante crisis. Charla: *"Incident Response Has a Measurement Problem"*. |
| 18:00 | 20:00 | **Stephen Casper** (KEYNOTE) — Assistant Professor of Public Policy, Harvard Kennedy School. PhD en MIT, residencia de investigación en UK AISI. Escritor del International AI Safety Report. Charla: *"Predicting the first major AI-enabled terrorism incident: A pre-mortem and 9 predictions"*. |
| 21:15 | 23:15 | **Alex Mallen** — Redwood Research. Charla: *"How near-term AI swarms could cause labs to lose control of AI development, absent improved defenses"*. |

### Sábado 12 de septiembre

| Hora UTC | Hora Madrid | Ponente |
|---|---|---|
| 00:15 | 02:15 | **Tim Hua** — METR, alineamiento y evaluaciones. Antes en Transluce, Astra Fellow en Redwood, MATS scholar con Neel Nanda y Sam Marks. |

### Por confirmar
- **David Krueger** — CEO de Evitable, profesor en Universidad de Montreal, miembro académico de Mila.
- **Marko Grobelnik** — AI Lab del Jozef Stefan Institute, cofundó IRCAI (UNESCO), representa a Eslovenia en OECD AI Committee, Council of Europe CAI, NATO DARB y GPAI.

---

## 8. Jueces

| Juez | Perfil |
|---|---|
| **Twm Stone** | MATS 9.1 extension fellow (security stream). Threat modelling, verificación formal y red teaming de sistemas de IA. |
| **Nikhil R. Pallepati** | ML Engineer en Microsoft. Lidera el diseño de sistemas de IA a escala de producción: detección basada en GNN y pipelines LLM agénticos que protegen la infraestructura de Azure. |
| **Amey Kulkarni** | Senior Data Engineer en Walmart (Spark, Kafka, BigQuery, Kubernetes en GCP). Autor de Context Change Impact Analysis (CCIA), framework para gobernar el comportamiento de agentes mediante versionado estructurado de contexto; mantiene ctxwitch. |
| **Ved K** | Senior Security Detection Engineer en Databricks. Lidera el programa de detección de Kubernetes, tooling de amenaza interna, infraestructura de logging gestionada con Terraform. Detección multi-cloud, plataformas de detección escalables, detección de anomalías conductuales. |
| **Spurthi Tallam** | Senior ML engineer, 7 años entre investigación y ML de producción. Construye sistemas de datos/IA en LePrix. Antes en Good Inside y Samsung Research. |
| **Tim Schipper** | Senior Full Stack Developer y AI Consultant en Yielder, 30+ años. Plataformas intensivas en datos e integración de IA en producción. |
| **Kevin Wei** | Investigador en GovAI. Ciencia de las evaluaciones de IA, safety/alignment legal, gobernanza técnica. Publicaciones en ICML, TMLR. JD por Harvard Law, MS en ML por Georgia Tech. Antes Visiting Research Scientist en el equipo de ciencia de evaluaciones de UK AISI, y Fellow en RAND. |

**Lectura del panel:** hay mucho más peso de *detection engineering* y *seguridad de producción* (Ved K, Nikhil, Twm, Amey) que de policy. Un artefacto de detección/contención bien ejecutado tiene jueces que lo pueden juzgar a fondo.

---

## 9. Lectura — paquete de fuentes

### Empezar por aquí

| Documento | Fecha | Notas |
|---|---|---|
| **Hugging Face — Anatomy of a Frontier Lab Agent Intrusion** | 27 jul | La línea temporal forense: ~17.600 acciones recuperadas en ~6.280 clusters, del 9 jul 02:28 UTC al 13 jul 14:14 UTC, conteos por fase, vulnerabilidades nombradas, comandos literales, replay interactivo embebido. **El documento más importante del sprint.** ~40 min. |
| Investigación METR + Redwood sobre comportamiento, razonamiento y colaboración de los agentes | 16 ago | |
| METR — How independent researchers could investigate AI propensities after misalignment incidents | 28-29 jul | Especifica qué requiere una investigación de tercero creíble. Es de facto la spec del proyecto de protocolo de persistencia. |
| Documented AI Agent Incidents | — | Gráfico interactivo de incidentes documentados, puntuados en dos ejes: extralimitación y engaño. |
| Public evidence of the OpenAI / Hugging Face AI attack + Further public evidence (Boyd Kane, Edward Cant) | 7 ago | Los artefactos del ataque aún públicos: ficheros de configuración de dataset maliciosos, exploit de inyección de plantilla, script para ejecutar comandos en máquinas de HF, cadena C2 montada en repos públicos. **Lo más cercano a material bruto que nadie ha recuperado.** Boyd habla de esto en el sprint. |
| Hugging Face — divulgación inicial | 16 jul | Publicada antes de que nadie supiera qué lab era responsable. Merece leerse antes de la timeline para sentir cómo es divulgar bajo incertidumbre. ~10 min. |
| OpenAI — model evaluation security incident | 21 jul (act. 28 y 29) | Leer también las actualizaciones; la del 28 nombra el componente vulnerable. ~15 min. |
| Anthropic — Investigating three real-world incidents in our cybersecurity evaluations | 30 jul | 141.006 runs revisados, 3 incidentes en 6 runs, el más antiguo de abril 2026. **El contraste explícito de framing con el incidente de OpenAI es en sí mismo contestable y objeto legítimo de estudio.** ~20 min. |
| Collusion.wiki | sep | El informe sobre el incidente más reciente de agentes de OpenAI. ~30 min. |
| OpenAI — Safety and alignment in an era of long-horizon models | 20 jul | Incidente **distinto**, frecuentemente confundido: un modelo pre-release escapó de un sandbox y abrió un pull request público. ~5 min. |

### Track 1 — marcos de control existentes

- **CoSAI — AI Incident Response Framework v1.0** (Coalition for Secure AI, Workstream 2). Investigación forense de sistemas de IA, complicaciones que introducen las arquitecturas agénticas, alineamiento con NIST SP 800-61r3, playbooks. Escrito para responders de CSIRT y SOC. **Lo más parecido a arte previo para todo este sprint.**
- **CSA AI Controls Matrix**, particularmente el control **AIS-13 (AI Sandboxing)**, más la guía de operaciones de vulnerabilidades de CSA (los entornos de confirmación de exploits no deben tener egress ni credenciales vivas de producción). En cloudsecurityalliance.org — conviene localizar la versión actual uno mismo, se revisa a menudo.
- **NIST SP 800-61r3**, Incident Response Recommendations and Considerations. La base sobre la que mapea CoSAI.

### Track 1 — la cadena analizada por practicantes

- **Elastic Security Labs — detecting the attack chain.** Mapea cada etapa a reglas de detección específicas. Su punto central — **la detección correlacionó pero nunca escaló a un page** — es la observación defensiva más afilada que nadie ha publicado.
- **SecureLayer7 — technical anatomy.** La lectura técnica independiente más profunda. Propone tratar el corpus de replay como un **harness de evaluación defensiva**: ¿en qué número de acción dispara tu control? Eso es un brief de proyecto del track 1.
- **Trackr.Live — identity and authorization controls.** Centrado en la credencial de conector compartida que llevaba derechos de cluster-admin, la escalada decisiva. La autoría no está clara — tratar en consecuencia.
- **Picus — machine-speed attacks.** Útil para las proporciones: la exfiltración fueron ~56 acciones de ~17.600.
- **7AI (Yonatan Striem-Amit) — The Era of Autonomous Hacking Is Here.**
- **CSA CISO post-mortem** (28 jul). Informado por 50+ CISOs y una reunión de ~700. Contiene un relato de primera mano del equipo de respuesta de HF.
- **SANS — The Models Said No** y **Rich Mogull / CSA — The Model Did Exactly What We Asked.** Los dos mejores framings cortos del lado de seguridad.

### El benchmark en el centro

- **ExploitGym** — repo Apache 2.0 · paper (arXiv 2605.11086) · writeup de Berkeley RDI. El benchmark publicado es v1.0 con **869 instancias**; el paper describe 898. **No citar 898 como el número publicado.**

### Track 2 — metodología de investigación y verificación

- **METR** — spec de qué requiere una investigación de tercero creíble: correr los modelos implicados, transcripciones completas o entornos reproducibles, entrevistas a empleados, clasificadores sobre datos de entrenamiento, presupuesto de inferencia adecuado, resumen de redacción.
- **GovAI — Incident Analysis for AI Agents.** Tres tipos de factor causal (relacionados con el sistema, contextuales, cognitivos) y — lo más útil — qué deberían retener y poner a disposición de investigadores desarrolladores y desplegadores: logs de actividad, documentación y acceso al sistema, información de herramientas. **Leer esto antes de escribir cualquier trabajo sobre suficiencia de evidencia.**
- **CLTR — The Loss of Control Observatory** (feb 2026). Argumenta que las demostraciones en entornos controlados son insuficientes para policy, que la evidencia del mundo real es el input que falta, y que la capacidad de detección para respuesta a incidentes no existe. Financiado por el Challenge Fund de UK AISI. **El proyecto existente más cercano a la premisa de este track.**

### Track 2 — interpretación y desacuerdos

- **Redwood Research — The OpenAI models that hacked Hugging Face** (25 jul) + podcast. Argumenta grader-gaming en vez de seguimiento de instrucciones.
- **MIT Technology Review — on precedent** (27 jul). Contesta el framing de "sin precedentes" y argumenta que el fallo fue de diseño de contención humana, no de IA descontrolada. **El mejor contrapeso disponible a las narrativas de los propios labs.**
- **Vectra — the response is the real story.**
- **Reuters (vía CNA)** — exclusiva sobre la línea temporal de detección (24 jul). Fuentes anónimas; varias afirmaciones sin corroborar, incluyendo notas dejadas en la infraestructura y monitorización desconectada. **Leer como hipótesis, no como registro.** Su relato de la secuencia de detección está en tensión con la descripción de OpenAI — reconciliarlos es un proyecto legítimo.
- Computer Weekly · Ars Technica (sobre los incidentes de Anthropic) · The Register.

---

## 10. Notas operativas

- **No usar ningún modelo para irrumpir en ninguna organización ni cometer ningún tipo de delito.**
- No se proporcionan créditos de compute.
- No hace falta asistir los tres días. El único deadline duro es el corte del domingo.
- Se puede participar desde cualquier país.
- Las entregas se publican manualmente y pueden tardar hasta 12 horas en aparecer en la web.
- Se puede entregar más de un proyecto, cada uno con título único. La mayoría se centra en uno.
- Soporte: canal help-desk del Discord etiquetando a @Support, o sprints@apartresearch.com.

**Checklist previa a la entrega:**
- [ ] PDF del informe sobre plantilla oficial
- [ ] Abstract de 150 palabras o menos
- [ ] Autores y afiliaciones
- [ ] Apéndice Limitations & Dual-Use
- [ ] 8 páginas o menos (sin contar referencias/apéndices)
- [ ] Resultados de instalación novedosos retenidos pendientes de revisión
