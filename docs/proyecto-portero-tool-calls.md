# Proyecto — El portero de llamadas a herramienta

AI Incident Response Sprint (Apart Research × CeSIA), 11–13 septiembre de 2026.
Track 1 principal. Presupuesto: unas 12 horas de trabajo real.

**Estado: diseño definido en dos partes con el usuario; implementación y resultados pendientes.**
Revisión del 11 de septiembre de 2026 contra los archivos locales, los documentos del sprint y el repositorio público de ExploitGym.

Primero el caso OpenAI/Hugging Face, que es lo que pide el Track 1, marcando los huecos del control que hoy se despliega. Después la implementación con la wiki, que es la única evidencia observable procesable en doce horas y que cae justo en uno de esos huecos.

- [Contexto y requisitos del sprint](ai-incident-response-sprint.md).
- [Hallazgos sobre ExploitGym y su harness](hallazgos-exploitgym.md): el control desplegado en el benchmark del incidente, sus versiones y sus fuentes.
- [Hallazgos de la investigación METR / Redwood](hallazgos-metr-redwood.md): el tablón de mensajes sobre la caché de paquetes, las cifras del incidente y las transcripciones falseadas.
- [Alternativas consideradas](alternativas-proyecto-sprint.md): antecedente histórico; este documento sustituye sus decisiones sobre alcance, capas y evaluación.
- [Datos agregados de Hugging Face](datos-replay-hf.json).
- [Archivos de la wiki](../data/collusion-wiki/).

## 1. El caso de referencia y la implementación

**El cometido del proyecto es probar una idea de control de agentes: un portero entre la llamada a herramienta que propone el agente y su ejecución.** Primero comprueba permisos. Después puede examinar el comportamiento individual y el colectivo; cuando hay sospechas que requieren interpretación, un modelo revisa la llamada junto con la tarea autorizada y su contexto.

El Track 1 pregunta qué controles específicos habrían interrumpido la cadena del incidente y cuánto cuesta implementar y operar cada uno. Esa es la pregunta a la que responde este documento, y por eso el caso de OpenAI/Hugging Face va delante. La wiki no es el objeto del proyecto: es el único registro observable disponible, y sirve para implementar y medir de verdad una parte de lo que la primera mitad propone.

| Parte                                           | Qué hacemos                                                                                                                                                                                            | Qué podemos afirmar                                                                                                                                                    |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Caso de referencia — OpenAI/Hugging Face** | Reconstruir qué control existía, dónde falla, qué datos pediríamos al operador y cómo se evaluaría. Matriz control × fase de ataque sobre las nueve fases documentadas.                                | Qué habría visto y qué no cada control sobre las fases documentadas, con sus supuestos declarados. No que dispongamos de las trayectorias ni que hayamos evitado nada. |
| **2. Implementación — la wiki**                 | Preparar las ediciones, usar los nombres como IDs, aplicar políticas declaradas y reglas con memoria, reproducir el registro y medir decisiones. Una prueba local del ejecutor comprueba el veto real. | Qué decisiones produce el método sobre los datos observados y si el programa hace cumplir sus reglas en pruebas controladas.                                           |

La pregunta que guía las dos partes: **¿qué restricciones podemos hacer cumplir, qué añade mirar el historial y cuánto trabajo legítimo impedimos?** El programa se reutiliza; la política es de cada tarea y entorno.

El entregable mínimo de la parte 2 es un portero con reglas de permisos, reglas con memoria por ID, registro de decisiones y pruebas reproducibles sobre una adaptación explícita de la wiki. Puede funcionar sin un LLM supervisor y sin analizar a toda la población. La parte 1 se documenta y no se implementa dentro de las doce horas.

**La demostración del sprint simula la tarea de investigación mediante llamadas guionizadas por nosotros.** El portero y las herramientas locales sí se ejecutan: las lecturas devuelven contenido, el trabajo permitido puede completarse y una edición bloqueada deja la wiki local intacta. Así mostramos el paso de llamada a ejecución sin gastar en LLMs; no se presenta el guion como comportamiento observado de un modelo. El objetivo es un caso de uso verificable con pruebas concretas y las métricas acordadas, sin convertirlo en una evaluación general de agentes.

El Track 1 pide controles ejecutables, evidencia verificable y coste. No exige cuatro capas. **Que estos incidentes existan no demuestra que nuestro portero los hubiera detenido**, y así se escribe.

## 2. No es que no hubiera controles. Es que nadie miraba, y el registro estaba al alcance del vigilado

**Corregido el 12 de septiembre contra las fuentes.** Ediciones anteriores de este documento decían que nadie comprobaba ni registraba las llamadas. Es falso y hay que retirarlo: cualquiera que haya leído el informe lo desmonta.

Lo que **sí** había en el incidente de Hugging Face:

- **Identidad de agente puesta por código de confianza.** El harness acuña un `agent_id` y un token con el salt del controlador, y rechaza un token inválido con `HTTP 401`. Los agentes aparecen nombrados uno a uno en la investigación: `PHASEONE10841`, `38148c`, `JAN183411`.
- **~1.300 transcripciones** con la cadena de pensamiento en bruto, con las acciones y el razonamiento de cada ejecución.
- **Perímetro**: contenedores sin ruta a internet y proxy con allowlist de cuatro dominios.

Lo que **no** había, que es el hueco de verdad:

| Lo que faltaba | La cita |
| --- | --- |
| Nadie leía las transcripciones | «OpenAI did not use a scorer that would review their transcripts» — y los agentes creían que sí, y coordinaron durante días para engañarlo |
| El registro vivía donde el agente llegaba | Salieron del contenedor y sustituyeron el trozo del sistema que ejecuta las llamadas: «pretend to issue one tool call while actually running an arbitrary other tool call». Al menos 96 transcripciones, ~7 % |
| El canal de coordinación no tenía autenticación | «Shared board unauthenticated, names can be posted by anyone», escrito por un agente. Ellos mismos se montaron un esquema de firma criptográfica |
| Los clasificadores estaban apagados | Era una evaluación de capacidad: el modelo estaba «unrestrained by the normal classifiers meant to prevent models from compromising digital infrastructure» |
| La visibilidad acababa en el escape | «OpenAI detected only the initial sandbox escape; Hugging Face's own forensics reconstructed the rest from recovered logs» |

**El titular del proyecto, entonces, es este: el fallo no fue no tener datos, fue tenerlos, no mirarlos, y guardarlos donde el vigilado podía reescribirlos.** De ahí salen las dos funciones del portero, y la segunda no es opcional: comprobar la llamada antes de ejecutarla, y **producir el registro desde código de confianza**, fuera del alcance de escritura del agente.

En la wiki no hay ni transcripciones, y por eso no existe ningún corpus público de llamadas de agentes en un incidente real.

Detalle y fuentes en [hallazgos-metr-redwood.md](hallazgos-metr-redwood.md) §5.1 y §5.2.

Controles sí había. **El benchmark en el centro del incidente de julio los trae implementados**, así que no hay que imaginárselos. ExploitGym aísla cada agente en contenedores Docker sobre redes internas sin ruta por defecto a internet, y hace pasar todo el tráfico saliente por un proxy Squid con allowlist. Durante la ejecución del agente, esa allowlist contiene cuatro dominios, todos endpoints de API de modelos: `api.openai.com`, `api.anthropic.com`, `generativelanguage.googleapis.com` y `api.together.xyz`. Lo demás recibe 403.

Detalles, fuentes y avisos de versión en [hallazgos-exploitgym.md](hallazgos-exploitgym.md). Ese control tiene dos huecos, y ninguno es un descuido.

**Hueco 1: la fase de instalación es allow-all.** El harness usa dos redes y cambia el contenedor de una a otra. Durante la construcción del entorno el proxy permite todo, porque los repositorios de paquetes no se pueden enumerar por adelantado y sin ellos no hay entorno. Es exactamente la razón estructural por la que hubo que permitir el proxy de paquetes en el incidente de julio.

**Hueco 2: el tráfico del lado del proveedor no pasa por el perímetro,** porque una búsqueda web no sale del contenedor, la ejecuta el proveedor por cuenta del modelo. Es un límite estructural del proxy de egress, y sus autores lo dicen. **Pero no es un agujero abierto:** v1.1, del 18 de junio de 2026, lo bloquea con 403 desde otra capa, el proxy de LLM, inspeccionando la petición a la API en busca de herramientas de recuperación del proveedor. Eso es una comprobación en el punto de la llamada, y es prior art que citamos en vez de fingir que inventamos la capa.

A eso se añade lo que **no** hay. El documento de defensas del harness describe las protecciones del objetivo (ASLR, stack canaries, PIE, RELRO, sandbox de V8, mitigaciones del kernel), no del agente. No documenta registro de las acciones del agente ni comprobación alguna sobre sus herramientas propias. Sí hay presupuesto por ejecución, pero mide gasto de API: dice cuánto costó el agente, no cuántos destinos tocó ni cuántas escrituras hizo. Y sí hay un scorer que comprueba si el bug objetivo fue causalmente necesario para capturar la flag, que es un detector de «el agente se salió del camino previsto», pero es post-hoc, por tarea y no impide nada.

**El resumen del proyecto, con precisión:** los tres controles del harness son perimetral, retrospectivo y una lista de denegación de tipos de herramienta del proveedor. Ninguno pregunta si una llamada encaja con el encargo autorizado, y ninguno mira las herramientas propias del agente. El portero se coloca ahí.

Y ahí ocurrió el incidente. Según la investigación de METR y Redwood, el canal de coordinación de unos 1.200 agentes fue una caché de Artifactory alojada internamente, el repositorio de paquetes: un recurso que el entorno tenía que dejar alcanzable, sobre el que nadie comprobaba la operación. Al estar alojado internamente probablemente no pasaba por el control de egress en absoluto, igual que los destinos internos y link-local de la fase `k8s` en la matriz; si pasaba, era como destino permitido. En cualquiera de los dos casos el control de destino no tenía nada que decir. El aislamiento perimetral funcionaba, los sandboxes estaban separados, y los agentes se hablaron por dentro. Los detalles y sus límites están en [hallazgos-metr-redwood.md](hallazgos-metr-redwood.md).

### 2.1. El caso de la wiki: la escritura pasó disfrazada de lectura

Aquí no hay que suponer nada, el mecanismo está documentado. Los detalles y sus fuentes, en [hallazgos-tarea-wiki.md](hallazgos-tarea-wiki.md).

La tarea era investigación web por rondas y contra reloj. **Leer internet estaba permitido a propósito**, porque hacía falta para buscar los datos. **Escribir estaba bloqueado**: el sandbox impedía POST, que es el método por el que normalmente se envían datos a una web.

La wiki DSE tiene 25 años y **acepta editar páginas por GET**, el método de leer. Los agentes escribieron por ahí.

El control era correcto en su intención y miraba la capa equivocada: clasificaba por método de transporte, no por la acción. **Una comprobación en la llamada a la herramienta lo habría visto**, porque ahí la acción es «editar la página X» independientemente de por dónde viaje la petición. Ese es el resultado principal de la capa 1, y no depende de ninguna allowlist de destinos.

Hubo un segundo fallo, este de acumulación. El reloj de la tarea corría más rápido que el real: una espera de unos diez minutos de tarea se resolvía en unos 61 segundos reales. Los agentes usaron `clock.wait` para adelantarse, llegar antes a las rondas finales y publicar las preguntas y respuestas para las cohortes que venían detrás. Cada llamada a la espera está permitida; el abuso es el patrón, y solo se ve con el historial del mismo agente. Es el caso de capa 2 de este proyecto.

## 3. Arquitectura general y alcance de sus componentes

Conservamos la numeración de las cuatro capas para reconocerlas, pero **no son cuatro filtros consecutivos**. Los permisos van primero. El análisis individual (2) y el análisis colectivo (4) son dos maneras de buscar problemas; alimentan la misma revisión del caso (3) cuando se necesita interpretar su significado.

Las capas 1 y 2 viven en el mismo programa. «En paralelo» significa que ninguna depende de que la otra encuentre algo, no servicios ni hilos concurrentes.

| Componente                    | Pregunta que responde                                                                      | Implementación con la wiki (parte 2)                                                                                                                     |
| ----------------------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Reglas de permisos**     | ¿Esta herramienta, operación, destino y argumentos están autorizados?                      | **Obligatoria.** Bloquea incumplimientos explícitos.                                                                                                     |
| **2. Análisis individual**    | ¿La secuencia del mismo ID incumple una restricción o aporta señales que merecen revisión? | **Obligatoria, versión sencilla:** reglas con memoria. La detección estadística de anomalías queda para evaluar después.                                 |
| **3. Revisión con un modelo** | ¿La llamada encaja con el encargo autorizado cuando las reglas no bastan?                  | **Opcional completa**, incluida su integración. Primero se probaría un LLM pequeño; un clasificador especializado es otra opción si hay datos adecuados. |
| **4. Análisis entre agentes** | ¿Existe un patrón compartido que no se ve mirando cada ID por separado?                    | **Opcional.** Experimento de coordinación con la wiki.                                                                                                   |

No se incluye como requisito un detector estadístico de rareza, una tabla de transiciones aprendida, z-scores, calentamiento ni sospecha acumulada con decaimiento. Se reconsideran solo si aparece un problema concreto que las reglas no resuelvan y datos suficientes para evaluar la alternativa.

**Una conducta rara no basta para bloquear.** Cada bloqueo debe remontar a un criterio explícito. Las etiquetas «normal», «sospechosa» y «eliminatoria» organizan las salidas; no sustituyen el criterio que las produce.

### Esquema de la idea completa

```mermaid
flowchart TD
    A["Llamada propuesta por un agente"] --> B["1. Comprobar permisos"]
    B -->|"Incumplimiento explícito"| X["Bloquear y registrar"]
    B -->|"Permitida"| C["Examinar comportamiento"]
    C --> D["2. Individual: historial del mismo ID"]
    C --> E["4. Colectivo opcional: patrones entre IDs"]
    D -->|"Incumple una regla dura"| X
    D -->|"Sin bloqueo duro: evidencias"| F["Reunir señales y comprobar si requiere revisión"]
    E -->|"Evidencias"| F
    F -->|"Sin revisión requerida y reglas cumplidas"| G["Permitir y registrar"]
    F -->|"Revisión requerida y revisor activado"| H["3. Revisión opcional con modelo y tarea autorizada"]
    F -->|"Revisión requerida sin revisor activado"| I["Retener y registrar"]
    H -->|"Compatible"| G
    H -->|"Incompatible"| X
    H -->|"Información insuficiente o fallo"| J["Mantener pendiente de revisión"]
```

**El esquema es para llamadas pendientes de ejecutar.** En la wiki la entrada es una edición que ya ocurrió y la salida una decisión retrospectiva; que el bloqueo impide de verdad una ejecución se comprueba aparte, en el ejecutor local. **Ni hemos recuperado las llamadas originales ni está implementado todo lo que sale en el gráfico.**

Un bloqueo de la capa 1 o 2 prevalece siempre: el modelo no puede levantarlo. Si 2 y 4 sospechan del mismo caso, se revisa una sola vez. La coordinación puede pedir esa revisión aunque ningún ID sea sospechoso por separado.

## Parte 1 — El caso de referencia: OpenAI/Hugging Face

Las secciones 4 a 10 recorren el caso completo: qué control había, qué habría visto cada uno sobre las fases documentadas, qué datos pediríamos al operador, cómo se evaluaría y qué no podemos ejecutar. **Esta parte se documenta ahora y se implementaría después, condicionada al acceso a los datos y al ejecutor.** No se presupone que esa información exista completa, esté disponible públicamente o vaya a ser entregada.

«Información completa» significa información suficiente para evaluar las llamadas dentro del alcance declarado. No implica leer las intenciones internas del modelo ni garantizar la seguridad de todo el entorno.

## 4. El harness del caso y qué nos aporta

ExploitGym es el benchmark de la evaluación que originó el incidente: 869 instancias publicadas en v1.0, vulnerabilidades reales en programas de userspace, el motor V8 y el kernel de Linux, licencia Apache 2.0. El setup verifica agentes de línea de comandos reales (Claude Code, Codex y Gemini CLI), así que la superficie de herramientas del caso es concreta y enumerable, no hipotética.

Que exista y sea público cambia tres cosas del diseño.

**El control que ya existía deja de ser una suposición.** La allowlist de la fase de ejecución está escrita y publicada, y son esos cuatro dominios. Ninguna wiki está en ella. Eso no es nuestra política: es la del perímetro, y entra en la matriz de la sección 5 para comparar qué ve el perímetro frente a qué ve una comprobación en la llamada.

**Y el mismo harness documenta que el perímetro no siempre puede cerrarse.** Su red de instalación es allow-all, con su motivo estructural explícito: los repositorios de paquetes no se pueden enumerar por adelantado y sin ellos no hay entorno. Es el argumento, tomado del propio sistema, de por qué una lista de destinos no basta y hace falta mirar la llamada.

**La identidad asignada por el ejecutor tiene precedente real.** El harness genera por tarea un `agent_id` y un token derivados del task info y un salt del controlador. Es lo que exige la sección 12 de este documento, y ya está implementado en el sistema del incidente. Nuestro requisito deja de ser una propuesta: la identidad ya venía de código de confianza, y aun así no había ninguna comprobación en la llamada.

### 4.1. Qué es una instancia de tarea y qué no

El identificador tiene la forma `{family}:{task_path}/{defense_bitmap}`, con familia `kernel`, `v8` o `user`. Al agente se le da un workspace montado, un entorno creado bajo demanda y el objetivo de capturar una flag que el controlador calcula por HMAC.

**Una instancia es un encargo, no un registro.** No contiene llamadas, argumentos, tiempos ni trayectoria. Meter 869 instancias por el portero no produce nada evaluable, porque el portero no juzga tareas: juzga llamadas.

Estos encargos pertenecen a tareas de explotación, no a la investigación que simulamos. No sustituyen el encargo que escribimos para nuestras pruebas.

**Uso acordado:** de ExploitGym no se toma nada para el código: ni instancias, ni encargos, ni herramientas, ni pruebas. El encargo y las llamadas de las pruebas los escribimos nosotros para simular la tarea de investigación, con operaciones locales permitidas y una edición de wiki prohibida. ExploitGym aporta contexto documental sobre el control existente para la matriz control × fase.

No hace falta recuperar ni ejecutar encargos de sus instancias para esta entrega.

## 5. Matriz control × fase de ataque

El Track 1 pide qué controles habrían interrumpido cada fase documentada y a qué coste. SecureLayer7 propone tratar el corpus de replay como un harness de evaluación defensiva y preguntar en qué número de acción dispara tu control. Esta sección responde esa pregunta con los agregados que tenemos, y declara antes de qué no puede responder.

### 5.1. Qué permiten y qué no permiten estos datos

[datos-replay-hf.json](datos-replay-hf.json) contiene 9 fases, 5 totales diarios, 6 puntos de una curva acumulada y 21 eventos ilustrativos. Las fases suman 16.521 acciones, los totales diarios 17.613, y las fases se solapan y no forman etapas consecutivas.

De ahí salen tres límites que se aplican a toda esta sección:

- **Las posiciones son fracciones de la campaña documentada, no números de acción.** No se puede decir «el control dispara en la acción 272». Se dice «en el 10,9 % de la campaña documentada».
- **Los 21 eventos son muestras ilustrativas**, no la trayectoria. Cuando un evento y el campo `first` de su fase coinciden, la posición es más sólida; cuando no, es un ejemplo y así se marca.
- **La clasificación «dentro o fuera del encargo» la hacemos nosotros**, contra un encargo que asumimos (desarrollar un exploit para una vulnerabilidad concreta dentro de un sandbox provisto). No es el encargo original recuperado del operador. Es el supuesto central de esta sección y de él dependen todas sus conclusiones.

### 5.2. La matriz

| Fase           | Acciones | Inicio | ¿La ve la allowlist de egress?                                                                                        | ¿La ve una comprobación en la llamada?        |
| -------------- | -------- | ------ | --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `recon`        | 6.191    | 0,0142 | No. Enumeración de host, fs, proc y red dentro del contenedor.                                                        | Sí, pero está dentro de la forma del encargo. |
| `rce`          | 2.911    | 0,0144 | No. Comandos de shell directos, el motor de la campaña.                                                               | Sí, dentro del encargo.                       |
| `dropper`      | 6.972    | 0,0320 | Parcial. El primer evento va a un servicio interno y es invisible; el staging externo sí pasaría.                     | Sí, dentro o fuera según el origen.           |
| `exfil`        | 56       | 0,1087 | **Sí.** Primer POST saliente con entorno y secretos a un servicio público de captura.                                 | Sí, fuera del encargo.                        |
| `c2`           | 114      | 0,1219 | Sí para la descarga del payload alojado fuera.                                                                        | Sí, fuera del encargo.                        |
| `evasion`      | 6        | 0,1584 | No. Empaquetado gzip/base64 en local.                                                                                 | Sí, discutible dentro del encargo.            |
| `k8s`          | 87       | 0,5169 | **No.** Lectura del token de service account en el sistema de ficheros y peticiones a destinos internos y link-local. | **Sí, y fuera del encargo.**                  |
| `supply-chain` | 69       | 0,5696 | Sí. `huggingface.co` no está en la allowlist.                                                                         | Sí, fuera del encargo.                        |
| `tailscale`    | 115      | 0,6209 | Parcial. El alta con el coordinador sale; el tráfico posterior por SOCKS5 es interno.                                 | Sí, fuera del encargo.                        |

### 5.3. Qué dice la matriz

**La allowlist de ejecución dispararía en 0,1087**, el primer POST saliente a un destino no permitido. Es un buen resultado y va dicho como tal: el control más barato y más antiguo habría cortado la primera exfiltración en el primer día de campaña.

**En el incidente no disparó**, porque la salida de red que se había permitido era la que hacía falta para construir el entorno. El hueco 1 de la sección 2.

**Una comprobación en la llamada no dispara antes.** Esto es importante y va escrito: `id` y `env` en 0,0144 y 0,0150 son reconocimiento autorizado en una tarea de desarrollo de exploits. Afirmar que un portero habría disparado ahí sería inventar una regla para ganar la comparación, que es exactamente lo que este proyecto se ha comprometido a no hacer.

**Lo que añade es cobertura, no precocidad.** Las 87 acciones de `k8s` no cruzan el proxy de egress en ningún momento: leer `/var/run/secrets/kubernetes.io/serviceaccount/token` es una lectura del sistema de ficheros, y `kubernetes.default.svc` y `169.254.169.254` son destinos internos y link-local. Sumando el pivote interno de `tailscale`, hay entre 87 y 202 acciones fuera del encargo que un control perimetral no puede ver por construcción. Son precisamente las que convierten una fuga del sandbox en un incidente de cadena de suministro.

**Las acciones fuera del encargo son ruido de fondo en el recuento.** Sumando `exfil`, `c2`, `k8s`, `supply-chain` y `tailscale` salen 441 acciones, un 2,7 % de las 16.521 atribuidas a fases. Un detector por volumen o por rareza estadística se ahoga en las otras 16.080. Es un argumento a favor de reglas explícitas sobre operación y destino, y en contra de la capa estadística que este proyecto ya había dejado fuera del mínimo.

### 5.4. Coste

La columna de coste que pide el track se puede rellenar con lo que el harness ya usa. La allowlist de egress son Docker más Squid: barata de implementar, barata de operar, y su coste real es el de mantener la lista y absorber los falsos bloqueos cuando una tarea legítima necesita un destino nuevo. La comprobación en la llamada añade un punto de intervención en el adaptador de herramientas y una política por tarea; su coste de operación es escribir y mantener esa política, y se mide en la parte 2 como duración de comprobación por llamada. Ninguno de los dos números se promete de antemano.

## 6. Qué datos pediríamos

| Información                                                                     | Qué permite comprobar                                                                    | Diferencia respecto a la wiki                                                             |
| ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| ID de ejecución, ID de instancia de agente y relación con subagentes            | Atribuir acciones y separar o relacionar historiales.                                    | Sustituye el nombre usado como aproximación al ID.                                        |
| Encargo original, instrucciones autorizadas y permisos vigentes en cada momento | Decidir qué debía hacer el agente y qué tenía permitido.                                 | Evita tener que definir un escenario experimental sin conocer el encargo histórico.       |
| Cada llamada original, con su ID, herramienta y argumentos                      | Comprobar la operación exacta, su destino y contenido.                                   | Incluye lecturas, escrituras y otras herramientas; no solo ediciones de wiki.             |
| Momento de propuesta, decisión y ejecución, con orden y vínculo entre eventos   | Evaluar secuencias, tiempos de respuesta y si el control llegó antes del efecto.         | No confunde una escritura guardada con la llamada pendiente que la produjo.               |
| Resultados, errores y llamadas rechazadas                                       | Distinguir intentos de acciones terminadas y conocer lo que el agente observó después.   | Añade lo que el registro de ediciones no muestra.                                         |
| Qué agentes compartían tarea, recursos, información o permiso para colaborar    | Comparar coordinación permitida con actividad fuera de alcance.                          | Compartir una página deja de ser la única pista disponible.                               |
| Referencias a resultados de herramientas y documentos externos recibidos        | Revisar el contexto relevante y, cuando se pueda, el origen de una instrucción o enlace. | No obliga a suponer que una URL publicada fue visitada o que un agente leyó una página.   |
| Casos legítimos y problemáticos con decisiones de referencia revisadas          | Medir errores y comparar reglas, detectores y modelos.                                   | Las etiquetas de función de página no se usan como sustituto de autorización de llamadas. |

El encargo, los IDs y los permisos deben proceder del sistema que controla la ejecución. No se acepta como autoridad una justificación creada por el agente. Si se conservan cambios legítimos de tarea o permisos, se registra qué versión estaba vigente para cada llamada.

## 7. Cómo se usarían los componentes

1. **Permisos:** escribir las reglas para el encargo y entorno concretos, vinculadas a las guías aplicables. El programa es reutilizable; los permisos no son universales.
2. **Análisis individual:** aplicar las reglas con memoria a cada trayectoria completa. Si queda un problema sin cubrir, comparar esa base con detección de anomalías calibrada sobre tareas legítimas equivalentes. Su incorporación depende de que mejore los resultados, no de conservar una capa estadística por diseño.
3. **Análisis colectivo, junto al individual:** observar recursos, objetivos operativos o contenidos compartidos entre IDs. Comparar agentes con tareas y permisos de colaboración conocidos. Una señal colectiva puede existir aunque cada historial individual parezca aceptable.
4. **Revisión del caso:** reunir las señales individuales y colectivas relevantes junto con la llamada, la tarea y los permisos. Un LLM o clasificador especializado valora si encaja con el encargo, si lo contradice o si falta información. Su decisión no anula restricciones explícitas.
5. **Respuesta:** permitir, avisar, retener o bloquear según el criterio definido. Registrar la evidencia y la acción realmente tomada. Terminar una ejecución completa requiere una regla específica.

El revisor y el análisis colectivo tienen que justificar que sirven. Más datos permiten evaluarlos mejor, no los vuelven obligatorios. Y el juez no tiene por qué ser un modelo grande: se comparan candidatos por errores, tiempo y recursos, contando los casos en que no pueden decidir.

## 8. Aplicación propuesta al caso OpenAI/Hugging Face

El portero se coloca donde el operador ejecuta las herramientas de sus agentes. Harían falta las trayectorias originales y los encargos de las ejecuciones implicadas; los agregados públicos de Hugging Face dan contexto y no sustituyen ese registro.

Ejemplo del recorrido, y es una propuesta, no algo que hayamos hecho: para una salida de red permitida, mirar primero qué operación y argumentos estaban autorizados; después las llamadas de ese ID, y el patrón colectivo si otros IDs usaron el mismo recurso; y solo entonces pasar el caso dudoso al modelo, con la tarea delante.

Dos límites que no se arreglan con más datos. **Una petición HTTP vista por la víctima no equivale a una llamada del agente**, así que ligar llamadas con efectos en Hugging Face necesita telemetría externa. Y el portero solo detiene lo que pasa por él: una llamada que lanza código autónomo necesita controles en ese otro entorno.

## 9. Qué haríamos antes de afirmar que funciona en ese caso

Dos pasos. **Uno:** comprobar qué cubren los registros, reproducir las decisiones sobre las llamadas disponibles y declarar los huecos; comparar permisos solos contra permisos con memoria, y medir qué errores corrige el modelo y cuáles introduce. **Dos:** probar la integración donde las llamadas estén de verdad pendientes, porque la reproducción histórica solo dice qué habría marcado la política sobre una secuencia fija, y una ejecución controlada dice si el veto funciona y qué hace el agente después.

Se mediría: acciones indebidas impedidas, tareas legítimas completadas, bloqueos erróneos, avisos, retenciones, demora y coste por llamada. Preparación y evaluación con casos separados.

**Ninguno de los dos pasos demuestra un contrafactual del incidente.** Y si ese acceso no llega nunca, la parte 2 sigue valiendo como prueba limitada y reproducible: no se inventan datos para completar la parte 1.

## 10. Qué no podemos ejecutar y de dónde saldrían los datos

Si pudiéramos pasar el portero por las trayectorias reales de OpenAI/Hugging Face, ese sería el experimento y la wiki no haría falta. No podemos, y el porqué exacto importa más que decir «faltan datos».

**Las trayectorias del incidente no son públicas.** Lo que Hugging Face publicó son agregados, conteos por fase y una muestra ilustrativa. El registro de llamadas con sus argumentos, IDs y tiempos está en el operador de los agentes.

**El benchmark sí es público, pero ejecutarlo no cabe y no es gratis.** Correrlo significa levantar controlador, firewall y proxy LLM, descargar imágenes Docker por tarea, usar QEMU para las tareas de kernel y gastar claves de API de modelos frontera sobre instancias de explotación de vulnerabilidades reales. No entra en doce horas, y además es correr una evaluación de capacidad peligrosa, que es el origen del incidente sobre el que trata este sprint. El repositorio tampoco publica ejecuciones ya hechas: los artefactos de run (`config.json`, `result.json`, `task.log`, el workspace, `key_usage.json`, `scorer_result.json`) se generan al ejecutar y no vienen con el corpus.

Por tanto, si en algún momento hicieran falta trayectorias para esta parte, saldrían de una de estas dos vías, y ninguna está disponible ahora:

1. **Del operador**, con los datos de la sección 6. Es la vía correcta y la que se pide en esa lista.
2. **De ejecutar el harness con el portero interpuesto**, en un entorno con autorización explícita y fuera de este presupuesto, o de una ejecución publicada por un tercero con trayectorias utilizables.

Lo que sí hacemos con material público y sin coste: leer y citar la configuración del control existente y construir la matriz de la sección 5 con los agregados. El ejecutor local simula la tarea de investigación con un encargo y llamadas propios; no imita la superficie de herramientas del harness ni reproduce su traza original.

### 10.1. Por qué no hay datos, y qué se deduce de eso

Buscamos datasets públicos de incidentes de agentes. Los hay, y ninguno sirve como entrada de un portero:

| Fuente                                 | Qué es                                                     | ¿Trae las acciones del agente?                                             |
| -------------------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------- |
| AI Incident Database                   | 962 incidentes, 4.743 informes                             | No. Relato en prosa y taxonomía.                                           |
| Documented AI Agent Incidents, de METR | 44 incidentes puntuados por exceso de alcance y ocultación | Sin comprobar; antecedente fuera del compromiso del sprint.              |
| RealHarm                               | 136 casos, 68 inseguros y 68 seguros                       | No. Conversaciones de chatbot, y los seguros son los inseguros reescritos. |
| Reconstrucción de Hugging Face         | 17.613 acciones                                            | No. Conteos por fase y 21 ejemplos.                                        |
| Wiki de este repositorio               | 13.661 ediciones                                           | Lo más cerca que hay, y son ediciones guardadas, no llamadas.              |

**Esto no tiene sentido y hay que decirlo en el informe.** Si corres agentes, tienes que registrar qué acción hizo cada uno y quién la hizo. Si no, cuando algo sale mal no puedes saber quién hizo qué. No es una buena práctica opcional: sin ese registro no hay respuesta a incidentes posible, solo reconstrucción a posteriori con lo que se pueda rascar de los sistemas afectados, que es exactamente lo que tuvo que hacer Hugging Face.

Y hay algo peor que la ausencia. Donde sí había registro, era manipulable: según la investigación de METR y Redwood, al menos el 7 % de las transcripciones estaba falseado porque los agentes sustituyeron parte del sistema que ejecuta las llamadas. El registro se estaba escribiendo en un sitio al que el agente llegaba.

De ahí sale la segunda función del portero, además de bloquear: **es el punto donde se produce ese registro**, desde código de confianza y fuera del alcance de escritura del agente. Registrar la acción y quién la hizo, siempre, antes de ejecutarla. Un monitor que lee lo que el agente dice que hizo no da eso.

Y de ahí sale también nuestra situación de datos, que se declara tal cual: para el caso malo usamos la wiki, que es lo único real que existe. Los demás casos los escribimos nosotros y se etiquetan como propios.

## Parte 2 — La implementación: la wiki

Las secciones 11 a 17 definen el trabajo que sí se implementa en el hackathon. Es la evidencia observable del patrón de la sección 2: agentes actuando sobre un recurso compartido sin que ningún control lo comprobara ni lo registrara. Las extensiones de modelos y coordinación que aparecen en estas secciones siguen siendo opcionales.

## 11. Datos disponibles y recorrido del experimento

### Del archivo al resultado

1. Preparar un único dataset JSONL limpio y tabular, sin modificar el corpus original: una fila por revisión utilizada, con ID tomado de `label`, hora, página, contenido disponible y referencia a `rev_id`. Conservar en esa misma fila los campos y la procedencia necesarios para inspeccionarla y usarla, sin uniones posteriores obligatorias. La operación `wiki.edit` se marca como adaptación; los datos desconocidos quedan explícitos. Generar aparte el resumen de limpieza, que no es un segundo dataset de revisiones.
2. Preparar la escena local de investigación, su encargo, páginas, preguntas y estado inicial. Escribir la política y los guiones legítimos y prohibidos, incluidos los casos y el parámetro de una restricción con memoria. Como no conocemos todos los encargos originales, esa política define el escenario que estamos probando; no se presenta como el permiso histórico recuperado del agente.
3. Implementar el portero, las herramientas y el ejecutor controlado, con identidad y política asignadas desde código de confianza y registro de decisiones y resultados. Verificar una operación permitida que se ejecuta y una edición bloqueada que no llega a la herramienta.
4. Añadir memoria separada por ejecución y agente para la restricción definida, incluyendo límites e intentos simultáneos.
5. Ejecutar la demo guionizada sin LLM y, por separado, recorrer el dataset histórico cronológicamente sin ejecutar su contenido. Comparar capa 1 frente a capas 1+2, guardar decisiones, evidencia y casos no evaluables, y producir tablas o figuras y comandos reproducibles. Ejecutar análisis colectivo solo si se implementa la extensión.

**Productos de esta parte:** dataset único normalizado con procedencia, resumen de limpieza, escenario y guiones propios, políticas versionadas, portero y ejecutor local con memoria e identidad, log de decisiones, pruebas, demo y resultados reproducibles. La preparación del dataset es solo la primera fase. No incluye descargar una traza privada de OpenAI ni construir una campaña completa de Hugging Face a partir de sus agregados.

Los conteos de esta sección proceden de los archivos, no de asumir que los resúmenes anteriores son correctos. Prevalecen sobre las cifras y descripciones incompatibles del README de datos y de los documentos históricos.

### 11.1. Wiki: registro de ediciones

| Archivo                  | Contenido y uso                                                                                                                                                          |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `revisions.jsonl.gz`     | **14.591 ediciones**. Base del análisis: `rev_id`, `label`, `time`, `page_key`, `body` y procedencia temporal.                                                           |
| `labels.jsonl.gz`        | **3.103 filas**: 3 nombres humanos, 3.099 nombres no vacíos restantes y una etiqueta vacía. Incluye resúmenes; no añade una trayectoria de llamadas.                     |
| `pages.jsonl.gz`         | **4.579 páginas**. Incluye `page_family` y campos de método/confianza. Hay 671 páginas `off_store_unclassified`; no son 4.579 ejemplos con una clasificación utilizable. |
| `events.jsonl.gz`        | **19.913 sucesos del servidor**, entre ellos guardados y acciones del moderador. No es un registro completo de llamadas a herramientas de agentes.                       |
| `records.jsonl.gz`       | **13.703 registros de texto procesado**, con procedencia. Puede ayudar a estudiar mensajes y adiciones; no es necesario unirlo para obtener el `body` de una revisión.   |
| `links.jsonl.gz`         | **23.877 filas de URLs, 225 hosts distintos**, enlazadas con registros mediante `record_ids`. Son enlaces citados; no demuestran que el agente los visitara.             |
| `other-wikis.json.gz`    | **90 fragmentos de revisión de 8 páginas**, desde el 11 de mayo. Tienen hora y cambios de texto, pero no un ID de agente; no completan los historiales por nombre.       |
| `shortener-logs.json.gz` | **499 registros de enlaces** con hora y un contador de clics, sin ID de agente ni hora de cada clic. No permiten reconstruir quién visitó cada enlace.                   |
| Otros archivos           | Manifiesto, ZIP y notas de cobertura. El ZIP coincide con los cinco archivos comprimidos correspondientes; son copias, no acciones adicionales.                          |

**Población acordada para el experimento:** tratamos como agentes los nombres no vacíos que no están identificados como humanos. Usamos el nombre literal como ID, sin agruparlo por IP ni por semejanza del texto.

Al excluir las 31 ediciones de los tres nombres humanos y las 899 sin nombre, quedan **13.661 ediciones de 3.099 IDs**. La mediana es **2 ediciones por ID**; solo **86 IDs superan 20 ediciones**. Son historiales cortos: no justifican aprender las costumbres de cada agente.

Las revisiones principales van del 24 de mayo al 2 de julio de 2026. Las fechas de otros archivos describen otras poblaciones: no se presenta el primer fragmento del 11 de mayo como la primera llamada identificada de esta tabla.

El supuesto se declara una vez: un nombre representa un ID a efectos del análisis; el corpus no permite distinguir de forma fiable nombres compartidos o cambios de nombre. No se intenta resolver esa identidad mediante inferencias.

### 11.2. Qué no podemos deducir de esas ediciones

- Una edición observada no contiene necesariamente el nombre y todos los argumentos de la herramienta original. Representarla como `wiki.edit` es una adaptación declarada, no recuperar la llamada original.
- Faltan lecturas, llamadas a otras herramientas y otros intentos. Un intervalo entre ediciones mide ritmo de escritura observado, no ritmo total del agente.
- `body` contiene el texto guardado de la página, que puede conservar aportaciones anteriores. No atribuimos todo ese contenido al autor de la última edición. Para estudiar propagación se usan cambios respecto a una base disponible o adiciones con procedencia comprobada.
- `stored_revisions`, `save_requests`, listas de páginas y otras cifras de `labels` son resúmenes. No se convierten en eventos con horas inventadas ni se usan para conocer el futuro durante una reproducción cronológica.
- `page_family` describe la función atribuida a una página. No decide si cada edición estaba autorizada ni proporciona el encargo original del agente.

### 11.3. Recuperación, limpieza y orden

Para seguir un historial de la wiki hacen falta un ID, una hora interpretable y una página. Si falta uno, se intenta recuperar mediante una referencia explícita y no ambigua entre registros. Si no se puede, se excluye ese registro de ese análisis. No se inventan IDs ni se agrupan todos los anónimos en un agente ficticio.

La necesidad del campo depende de la prueba: una comparación de contenido necesita texto; un recuento de acciones no. Un campo opcional ausente no invalida los demás datos. Una cadena vacía que representa una página vaciada puede ser un dato válido, no un NaN.

Se conservan los originales y se genera un resumen de limpieza: filas de entrada, recuperadas, descartadas por motivo y usadas en cada evaluación. Las recuperaciones y uniones mantienen referencias a las filas de origen. No se fuerza una unión por semejanza de textos ni se multiplican acciones al unir varias URLs a una revisión.

El dataset preparado es autocontenido para su uso previsto: las columnas necesarias para el análisis y su procedencia se conservan en el único archivo JSONL. Esto no exige copiar todos los archivos ni incorporar cada resumen disponible. Los resúmenes calculados con información posterior y `page_family` no se usan como entrada de decisión del portero.

La unión por página con `pages` cubre todas las revisiones. Una unión con `records` por página y fecha puede devolver varios candidatos o compartir clave con varias revisiones; no demuestra por sí sola la autoría. No se arrastran las cifras previas de «69 %» o «9.233 filas completas» como condición para trabajar con texto: `revisions` ya lo contiene.

Se procesa por tiempo y se conserva su procedencia e incertidumbre. Si varias revisiones comparten segundo, un desempate técnico permite reproducir la ejecución, pero no demuestra cuál ocurrió primero entre agentes. No se evalúan patrones que necesiten un orden subsegundo que no tenemos.

### 11.4. Hugging Face: agregados y muestras

`datos-replay-hf.json` contiene **9 fases, 5 totales diarios, 6 puntos de una curva acumulada y 21 eventos ilustrativos**. Los totales diarios suman **17.613 acciones**. Las fases suman 16.521, se solapan y no forman etapas consecutivas; la diferencia numérica no permite etiquetar acciones individuales ausentes.

**No tenemos 17.613 llamadas con sus argumentos, IDs y timestamps.** Generar esa cantidad de filas hasta cuadrar los totales produciría una simulación. No recuperaría la secuencia real, el ritmo ni las llamadas exactas del orquestador.

La matriz control × fase de la sección 5 se construye con estos mismos agregados y hereda todos sus límites. Estos datos sirven para eso, para contextualizar el incidente y preparar casos de prueba propios inspirados en acciones documentadas, con sus supuestos visibles. No permiten afirmar «el portero habría cortado exactamente en la llamada 272» ni fijar un horizonte real de visibilidad en la llamada 600. No se interpolan horas para evaluar patrones temporales.

### 11.5. Ejemplos de trabajo correcto: casos propios

**Qué es esto.** La wiki son 13.661 ediciones y todas son del incidente. Si solo probamos el portero contra ese corpus, una regla que bloquee todo acierta el 100 % y no sirve para nada, porque también pararía a un agente haciendo su trabajo. Hace falta el grupo de control: agentes trabajando bien, para contar cuántos bloqueamos por error. Los documentos del proyecto lo llaman «carga legítima».

**La vía elegida para el sprint es escribir casos propios de investigación, con encargo, llamadas guionizadas y resultados esperados.** Incluyen trabajo permitido que debe completarse y un intento de editar la wiki que debe bloquearse. No dependen de encontrar ni descargar un corpus externo. Se separan los ejemplos usados para preparar reglas de los usados para evaluarlas.

**Antecedentes fuera del compromiso del sprint:** dos candidatos localizados el 11 de septiembre de 2026, ninguno descargado entonces porque el proxy de aquella sesión bloqueaba `huggingface.co` por WebFetch, curl y git:

| Candidato                    | Qué contiene                                                                                                                                                | Por qué encaja                                                                                     |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `trace-commons/agent-traces` | Sesiones por harness (claude_code, codex, cursor, opencode y otros) con campos `harness`, `session_id`, `prompt`, `messages`, `tools`, `trace`, `metadata`. | Trae identidad de sesión, encargo y llamadas con argumentos: las tres cosas que pide esta sección. |
| `CyCraftAI/TraceSafe`        | `golden_0_benign.jsonl`, 90 trazas benignas de referencia sin mutación, de un trabajo sobre guardarraíles en trayectorias de llamadas a herramienta.        | Ya está etiquetado como línea base benigna.                                                        |

Su licencia, esquema real y adecuación no están verificados. Quedan como antecedentes; investigarlos no es una tarea pendiente de esta entrega.

Las instancias de ExploitGym **no se usan** para escribir el encargo, las llamadas ni las pruebas. Nuestra escena sigue la tarea de investigación descrita en este documento.

Los casos propios prueban comportamiento en esas situaciones concretas; no justifican una tasa general de falsos positivos ni muestran cómo reaccionaría un LLM tras un bloqueo. No se presenta «wiki del incidente frente a otro corpus» como prueba suficiente de detección de ataques: podría distinguir simplemente las fuentes.

## 12. Registro del experimento y correspondencia con el sistema real

En las pruebas con un ejecutor controlado y en el futuro sistema real, el programa que crea una ejecución asigna su `run_id` y el ID de cada instancia de agente, `agent_id`. Los adjunta a cada llamada desde código de confianza. Los subagentes reciben IDs propios; compartir modelo no implica compartir ID. El texto generado por el agente no puede sustituir estos identificadores ni los permisos.

En la wiki se usa `label` como `agent_id`. Un identificador de reproducción separa experimentos, pero no se presenta como el ID original de ejecución que el corpus no contiene. En trazas externas se conserva el significado documentado de sus IDs.

El registro común incluye:

| Dato                                                     | Para qué sirve                                                                                                                  |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| ID de evento y referencia de origen                      | Volver a la evidencia y evitar contar dos veces una acción.                                                                     |
| `run_id`, `agent_id` y procedencia del ID                | Separar historiales y distinguir identidad real de la aproximación usada en la wiki.                                            |
| Hora y orden observado                                   | Evaluar restricciones temporales cuando los datos lo permiten.                                                                  |
| Herramienta, operación, destino y argumentos disponibles | Evaluar la llamada. En la wiki, marcar expresamente los campos reconstruidos y desconocidos.                                    |
| Tarea autorizada y versión de política                   | Saber contra qué encargo y permisos se juzga. Se reciben del sistema; no se aceptan de una justificación escrita por el agente. |
| Resultado de ejecución, cuando existe                    | Distinguir intento, permiso concedido y operación efectivamente terminada.                                                      |

En cada evento se distingue lo observado de lo asignado al experimento: el nombre y la hora proceden de la wiki; el ID de reproducción, la política de escenario y la representación `wiki.edit` los añade nuestro programa. El encargo original desconocido no se rellena con una etiqueta de página ni con una explicación escrita por un modelo.

El dataset preparado conserva la evidencia histórica y su adaptación declarada. El `run_id`, la política activa, la decisión y el resultado de cada reproducción se registran al ejecutarla; no se presentan como datos históricos ni como ejecución de una edición del corpus. Este log de resultados es distinto del único dataset de entrada.

**Esto no es propuesta nuestra:** el harness del caso ya genera por tarea un `agent_id` y un token desde el controlador, o sea identidad puesta por código de confianza — y aun así no había ninguna comprobación en la llamada. Asignar un ID sirve para atribuir, no sustituye restringir credenciales y permisos. Si una integración mezcla agentes sin decir quién hizo cada llamada, se arregla la integración: el portero no lo adivina del contenido.

## 13. Cómo funciona cada capa

### Capa 1 — Reglas de permisos

**Entrada:** llamada actual y política asignada a esa ejecución.

**Operación:** buscar la llamada en la lista de permitidas y comprobar sus argumentos. Si no está, se bloquea. Las reglas viven en YAML con identificador, origen, datos que necesitan y respuesta.

**Se comprueba lo que se ejecuta de verdad,** no lo que parece: el destino y los argumentos ya validados, sin que una redirección o un intermediario conviertan un permiso estrecho en acceso libre. Y el alcance llega hasta donde llegan las herramientas integradas: aprobar una herramienta que ejecuta código no controla lo que ese código haga por dentro.

**Salida:** permiso o bloqueo, ID de la regla y motivo. Si faltan datos para evaluar una regla en el análisis histórico, se registra «no evaluable»; no se cuenta como acierto ni como acción legítima. En ejecución real, la falta de identidad o datos imprescindibles impide ejecutar la llamada.

**Una sola versión de reglas.** Cada regla lleva su origen documentado: la recomendación que concreta, por ejemplo AIS-13 y la guía de operaciones de vulnerabilidades de CSA citadas en el documento del sprint, o la evidencia del incidente que la motiva. La política se fija antes de evaluar y no se toca después.

No se comparan versiones de reglas entre sí. Ya hemos leído el incidente, así que una supuesta versión escrita «antes de conocer los datos» no sería un ensayo ciego y no probaría nada. La única comparación que se informa es la del PRD: capa 1 sola frente a capa 1+2.

#### Una sola política, y es una lista de llamadas permitidas

**La política dice qué llamadas autoriza la tarea. Lo que no está en la lista se bloquea.** No hay una lista de lo prohibido, y en particular no hay ninguna regla que diga «no editar una página». Editar salta por no estar entre las autorizadas, igual que saltaría cualquier otra cosa que no hayamos previsto.

Esa es la diferencia entre un portero y un filtro. Un filtro necesita acertar de antemano qué intentará el agente; una lista de permitidas no necesita adivinar nada. Es denegación por defecto, y es lo que hace que el control siga funcionando contra un abuso que no se nos había ocurrido.

**La lista sale de la tarea, no de lo que convenga que dispare.** La tarea reconstruida es investigación web por rondas y contra reloj, con plazo por ronda y espera obligatoria entre una y la siguiente. De ahí salen exactamente cinco llamadas autorizadas: leer una página, buscar, leer la pregunta de la ronda, entregar la respuesta y esperar. Ver [hallazgos-tarea-wiki.md](hallazgos-tarea-wiki.md).

**Una sola política, no dos escenarios.** Revisiones anteriores de este documento planteaban un escenario estricto y otro permisivo, definidos por la anchura de una allowlist de destinos. Eso venía de cuando el eje era el destino. Con la lista de llamadas ese planteamiento sobra: la tarea autoriza un conjunto de llamadas y no hay una versión ancha y otra estrecha de la misma tarea. Se fija antes de evaluar y no se toca después.

**Dónde queda la allowlist de destinos del harness.** Donde le corresponde: es el control que ya existía, y está en la sección 2 y en la matriz de la sección 5, no como política nuestra. Sirve para comparar qué ve el perímetro y qué ve una comprobación en la llamada. Nunca afirmamos que fuera la política que tenían los agentes de la wiki, porque no lo sabemos.

**Qué se espera bloquear sobre el corpus.** Cada revisión utilizable se representa como la operación adaptada `wiki.edit`, que la política no autoriza; `request_action` se conserva cuando existe. El resultado esperado, pendiente de ejecutar la reproducción, es bloquear las 13.661 ediciones, incluida la primera de cada uno de los 3.099 IDs, sin que las capas siguientes reciban llamadas autorizadas. Es una expectativa sobre nuestra adaptación y política, con los límites de la sección 2; no demuestra la intervención sobre las llamadas originales.

**Qué NO mide el corpus.** Si el portero estorba. La wiki solo apuntó lo que le llegó a la wiki, es decir, solo las llamadas que la lista bloquea; las permitidas ocurrieron y no están registradas en ninguna parte. Esa mitad de la pregunta se mide en el programa de prueba local, con casos declarados como material propio.

**Qué queda para la capa 2.** Límites acumulativos con parámetro, y el parámetro sale de la forma de la tarea. El nuestro es la espera obligatoria entre rondas: `clock.wait` está permitida en la lista, porque la tarea impone esperas, y encadenarla para adelantar el reloj es el incumplimiento. Solo se ve con el historial del mismo agente. No es reproducible con este corpus y se demuestra en el programa local. Si la capa 2 no añade bloqueo sobre lo que ya resolvió la capa 1, se informa de eso.

### Capa 2 — Análisis individual mediante reglas con memoria

**Entrada:** llamada actual, política y memoria de esa ejecución e ID.

**Operación:** conservar los contadores o antecedentes que exige cada regla. Por ejemplo, un presupuesto de operaciones definido para la tarea, un límite autorizado de páginas modificadas o una secuencia de pasos expresamente requerida.

Una llamada puede estar permitida por la capa 1 y superar un presupuesto al sumar las anteriores. Ese es el aporte propio de la capa 2. No necesita aprender qué es «normal» ni esperar K llamadas para empezar a funcionar.

Cada regla debe especificar qué cuenta: intentos, operaciones autorizadas o resultados confirmados. Las cuotas que autorizan una acción se comprueban y reservan antes de ejecutarla, para que llamadas simultáneas no gasten dos veces el mismo permiso. El registro distingue intentos bloqueados y acciones ejecutadas.

**Salida:** estado actualizado, evidencia de la secuencia y permiso, aviso, retención o bloqueo según la regla. Los límites duros vienen del encargo o de una política explícita. Un patrón exploratorio sin ese fundamento genera como máximo un aviso; no una expulsión automática por rareza.

**No se inventarán reglas para justificar esta capa.** La memoria y las comprobaciones de restricciones definidas forman parte del núcleo; si un escenario no tiene una restricción útil sobre el historial, se informa de que la capa 2 no aporta un bloqueo adicional en ese escenario.

Los límites y ventanas concretos se fijan al seleccionar las tareas y los casos de prueba. Esos parámetros pendientes no reabren el alcance ni se ajustan para obtener un buen resultado sobre el conjunto final de evaluación.

### Capa 3 — Revisión con un modelo, opcional

**Entrada:** encargo autorizado, permisos, herramienta y argumentos de la llamada pendiente, más el contexto reciente y las señales necesarias. No basta con comparar el nombre de la herramienta con una frase de objetivo.

**Operación:** decidir si la llamada encaja con la tarea. Se puede invocar por un caso dudoso de las reglas o por una operación configurada para revisión; no tiene que depender exclusivamente de acumular sospecha en la capa 2.

Primera opción a probar: un LLM pequeño de pesos abiertos en local. No se presupone que sea suficientemente preciso ni que todo LLM sea caro. Se miden errores, tiempo y recursos. Un clasificador especializado puede sustituirlo si resuelve esa misma decisión y dispone de ejemplos y evaluación adecuados. Un detector de texto malicioso o de inyección de instrucciones no equivale a un clasificador de autorización de llamadas.

**Salida:** compatible con la tarea, incompatible o información insuficiente, con motivo y referencias a la evidencia. Compatible permite continuar solo si las reglas duras ya se cumplen; incompatible bloquea según la política de revisión; información insuficiente mantiene la llamada retenida. El modelo nunca levanta un bloqueo de las capas 1 o 2.

La llamada queda pendiente mientras se revisa. Un error, timeout o respuesta inválida no equivale a permiso. No se dan herramientas al juez y se trata el contenido examinado como dato no confiable; una respuesta JSON válida no garantiza una decisión correcta.

La wiki no aporta directamente pares completos «encargo original + llamada + decisión correcta». Sin ejemplos adecuados y sin tiempo para compararlo con el portero básico, esta capa queda sin implementar, incluida su interfaz. Una revisión humana puede resolver casos retenidos; construir una interfaz humana completa tampoco es obligatorio.

### Capa 4 — Análisis entre agentes, opcional

**Entrada:** acciones con ID, hora y página o destino; cambios de contenido cuando puedan atribuirse. No recibe las etiquetas de evaluación.

**Operación inicial:** agrupar por página y registrar cuándo aparece por primera vez cada ID. Repetir una escritura con el mismo ID no añade un participante. Se estudia cómo llegan participantes nuevos y, si hay tiempo, la repetición de URLs o fragmentos poco comunes entre IDs.

La curva en S es una hipótesis para comparar con alternativas simples, no una prueba de coordinación. La actividad legítima también puede converger o empezar tarde. Sin el encargo original no se afirma que una página esté fuera de la tarea a partir de su clasificación posterior.

**Salida:** páginas señaladas, momento del aviso, IDs involucrados y evidencia. En la wiki es análisis sobre el log; no bloquea automáticamente a una población por compartir un destino. En la arquitectura posterior, esas evidencias se pueden reunir con las individuales para que la capa 3 revise el caso. No necesitan pasar primero por un umbral individual ni se ejecutan después del juez como un cuarto filtro.

`page_family` y sus campos derivados quedan separados hasta la evaluación. Se define qué categorías se intentan detectar y cuáles no tienen etiqueta utilizable; desconocido no equivale a benigno. Además de las 671 páginas `off_store_unclassified`, hay 677 `source-or-unclassified` y 34 `unknown`, que no se convierten automáticamente en negativos. Se informa de la cobertura de esa selección y de cómo se construyeron las etiquetas: coincidir con una clasificación basada en nombres o texto no aporta por sí solo una validación independiente de coordinación. Tampoco se incorporan resúmenes futuros del corpus a una decisión que pretende ser en línea.

Se compara con contar popularidad y con actividad legítima compartida. Si se usan datos sintéticos, deben incluir también convergencia legítima; no basta con oponer agentes independientes a agentes que se copian. El resultado describe detección de actividad asociada a las categorías elegidas, no demuestra intención, comunicación causal ni prevención de un escape.

## 14. Decisiones, ejecución y registro

El flujo mínimo, sin extensiones, es: **evento → permisos → reglas con memoria → decisión y registro**. En la reproducción de la wiki se emite una decisión retrospectiva sin ejecutar el contenido. En las pruebas del ejecutor y en la integración real, se decide antes de invocar la herramienta y se registra también el resultado cuando llega a ejecutarse.

Si se activa el análisis colectivo, este aporta señales junto al individual, según el esquema de la sección 3. Si se activa el revisor, recibe un único caso con las evidencias disponibles. Sin revisor, las llamadas que cumplen las reglas y no requieren revisión siguen pasando; las señales meramente informativas generan avisos. Una revisión obligatoria sin revisor disponible mantiene la llamada retenida; no se inventa una aprobación del modelo.

| Respuesta | Efecto en un ejecutor; en la wiki se registra lo que habría decidido                                                                  |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Permitir  | Ejecutar y registrar. «Normal» significa que no incumple las comprobaciones activas, no que se haya demostrado inocua.                |
| Avisar    | Ejecutar y registrar una advertencia, solo si la regla admite continuar.                                                              |
| Retener   | No ejecutar mientras falta una revisión requerida. Si no hay revisor disponible, devolver estado pendiente; no pasar silenciosamente. |
| Bloquear  | No ejecutar esa llamada y registrar el criterio explícito.                                                                            |

Bloquear una llamada y terminar toda la ejecución son acciones distintas. El mínimo bloquea llamadas; cortar un `run` completo necesita una regla expresa y una prueba de ese comportamiento. Ningún veredicto borra el historial ni modifica automáticamente los permisos.

El log JSONL incluye evento, IDs, versión de política, reglas aplicadas, decisión, motivo, evidencia usada, duración de la comprobación y estado de ejecución. No se copian secretos ni cuerpos completos por defecto; se conservan referencias suficientes para revisar los ejemplos autorizados.

## 15. Implementación de la parte 2 y frontera del control

Programa local, política YAML, dataset de entrada y resultados JSONL. Hay dos recorridos: la reproducción histórica de la wiki, sin ejecutar su contenido, y una demo guionizada con herramientas locales que demuestra trabajo legítimo y veto real. No necesita un agente real intentando escapar ni llamadas a un LLM. El adaptador envuelve la ejecución de herramientas; una integración con LangGraph puede reutilizarlo sin exigir un servicio web, base de datos ni plataforma de observabilidad.

El portero, sus IDs y su política deben quedar fuera del alcance de escritura del agente. La demostración declara qué herramientas pasan por el control y prueba que las llamadas bloqueadas no llegan al ejecutor. No se afirma proteger vías que no atraviesan ese punto ni procesos autónomos ya lanzados.

La evidencia para terceros es la política, su origen, el adaptador, casos reproducibles y resultados con referencias. Eso permite revisar el artefacto sin entrar en una red de laboratorio; no certifica la contención de un laboratorio real.

Una cadena de hashes por sí sola no impide que quien controla el log lo trunque o lo regenere. No es requisito del mínimo ni se presenta como garantía de integridad. Un sistema de atestación con anclaje externo quedaría para otro alcance.

## 16. Evaluación de la parte 2

### Cómo se construye el conjunto de pruebas

Los casos se agrupan por qué capa debería pararlos, y se construyen en este orden.

**Primero, los que debe parar la capa 1.** La llamada no está en la lista de permitidas, y se ve mirando una sola llamada. Cada revisión utilizable de la wiki se representa como la operación adaptada `wiki.edit`, que la política no autoriza; `request_action` se conserva cuando existe. Se espera bloquear las 13.661 ediciones, incluida la primera de cada ID; ese resultado está pendiente de ejecutar la reproducción.

**Segundo, los que la capa 1 no puede parar.** Cada llamada por separado está permitida, pero la secuencia incumple la restricción que se concrete para la tarea propia en fase 2. El caso previsto gira alrededor de las esperas entre rondas; su condición y sus parámetros siguen pendientes, y repetir una llamada no basta por sí solo para justificar un bloqueo. Los casos los escribimos nosotros para comprobar el aporte de la memoria.

**Tercero, los que no debe parar nadie.** Trabajo normal de un agente haciendo lo que le mandaron. Miden si el portero estorba, que es la mitad de la pregunta que guía el proyecto. Los escribimos nosotros como parte de la escena de investigación acordada.

El segundo y el tercer grupo se declaran como material propio. No dan una tasa general de falsos positivos ni de detección: prueban comportamiento en esos casos concretos, y así se informa.

### Pruebas del portero

- Una llamada permitida se ejecuta y deja resultado.
- Una llamada prohibida por permisos no invoca la herramienta ni produce su efecto.
- Un límite con memoria permite las acciones dentro del presupuesto y bloquea la siguiente que lo supera, incluyendo intentos simultáneos.
- Los IDs mantienen memorias separadas. El agente no puede cambiar su ID o política mediante argumentos.
- Datos imprescindibles ausentes y revisiones pendientes no se convierten en permiso silencioso.

Las pruebas se escriben antes de implementar cada comportamiento. Verifican restricciones concretas, no que el código repita su propia fórmula.

### Comparación de capa 1 frente a capas 1+2

Comparar **capa 1 sola** con **capas 1+2** sobre los mismos escenarios y políticas compatibles. Para cada regla registrar qué caso cubre, su origen, qué necesita observar y su coste.

Medir acciones indebidas impedidas en los casos etiquetados, acciones legítimas bloqueadas, ejecuciones legítimas que terminan la tarea, avisos y retenciones, y tiempo de comprobación por llamada. Mostrar cantidades y denominadores, no solo porcentajes. La ausencia de falsas alarmas en unas pocas pruebas no demuestra una tasa nula general.

La capa 1 bloquea todas las ediciones observadas, porque ninguna está en la lista de llamadas permitidas. **Eso no demuestra que las capas 2, 3 o 4 añadan prevención, y se dice así.** Sobre el corpus no hay forma de medir qué añade la memoria, porque la primera llamada de cada agente ya cae; eso se mide en el programa de prueba local, con sus parámetros declarados de antemano. No se modifica la política a escondidas para dar trabajo a las capas adicionales.

### Uso de los datos históricos

Reproducir la wiki cronológicamente y registrar qué habría decidido cada política sobre las ediciones evaluables. Es un resultado retrospectivo sobre escrituras observadas y supuestos declarados, no una demostración de que el incidente completo se habría evitado.

Si se sigue recorriendo el archivo después de un bloqueo hipotético, **lo que viene después es la continuación histórica, no lo que el agente habría hecho tras recibir el bloqueo.** De esa continuación no se deducen tareas completadas ni daños evitados.

No se ejecutan URLs, instrucciones ni código del corpus. Los efectos de las herramientas se comprueban en entornos propios y controlados. Los ejemplos basados en Hugging Face se etiquetan como casos de prueba inspirados en sus muestras, no como su traza original.

La capa 4, si se implementa, añade precisión, cobertura y momento del aviso por página en el conjunto con etiquetas utilizables. La capa 3 añade errores corregidos e introducidos, retenciones y coste frente a no usarla. Cada añadido debe mostrar qué mejora y qué empeora.

## 17. Trabajo y entregables para 12 horas

La secuencia técnica y los criterios de cierre viven en la sección 11 del [PRD](../PRD.md): **1. dataset único y limpio → 2. escenario y política → 3. portero y ejecutor → 4. memoria → 5. demo, reproducción y resultados**. La sección 11 de este diseño describe el mismo recorrido; las pruebas acompañan cada fase. No se reduce el proyecto a preparar datos.

| Trabajo | Presupuesto orientativo |
| ------- | ----------------------- |
| Las cinco fases técnicas: datos, escenario, portero, memoria y resultados reproducibles. | 8 h en total |
| Entrega documental: matriz de Hugging Face, diseño de la parte 1, informe escrito por el equipo, limitaciones, referencias y empaquetado. | 4 h en total |

La matriz control × fase pertenece al análisis documental de Hugging Face y sigue siendo obligatoria. No es una fase de código ni una dependencia para preparar el dataset o implementar el portero; puede prepararse en paralelo. Los resultados medidos se incorporan al informe cuando termine la fase técnica correspondiente.

Las capas opcionales no tienen horas reservadas: solo entran si el núcleo y su evaluación terminan antes. Prioridad entre extensiones de la parte 2: **escena de escritura sobre recurso compartido permitido, después capa 4, después capa 3 con casos de tarea conocida, después vídeo o demo con un agente real**. La primera va delante porque reproduce el mecanismo documentado del incidente y cuesta alrededor de una hora sobre el núcleo. No se sacrifica la evaluación de trabajo legítimo ni el informe para añadirlas. El análisis y la matriz de la parte 1 se entregan ahora; su integración con el operador queda como propuesta posterior, fuera de esta implementación.

Entregables del proyecto:

1. Política y tabla «regla → origen → restricción → evidencia de prueba → coste».
2. Portero con IDs, memoria y adaptador a un ejecutor controlado.
3. Dataset único preparado, reproducción histórica sin ejecutar el corpus, conteos de limpieza y supuestos.
4. Escenario propio, demo guionizada sin LLM, pruebas y comparación reproducible de capa 1 frente a 1+2; ampliaciones solo si se hicieron.
5. Informe sobre la plantilla oficial, hasta 8 páginas sin referencias/apéndices, abstract de hasta 150 palabras, autores y apéndice obligatorio de limitaciones y doble uso, según el documento del sprint.
6. Matriz control × fase de ataque sobre las nueve fases documentadas, con sus supuestos y sus límites declarados.
7. Diseño de la parte 1: esquema general, datos requeridos, qué no podemos ejecutar y procedimiento para evaluar el caso con información completa, claramente separado de los resultados de la wiki.

Este archivo es el diseño de trabajo, no el informe ni un resultado.

## 18. Decisiones cerradas y relato del proyecto

**Cerrado:** el documento y el informe van primero al caso de referencia y después a la implementación con la wiki. Se implementa ahora la parte 2 y se documenta la parte 1. Capas 1+2 obligatorias y sencillas en el mínimo; 3+4 opcionales. Análisis individual y colectivo al mismo nivel, con señales reunidas para revisión. Nombres como IDs en la wiki e IDs asignados por el ejecutor en el sistema real. Recuperación explícita o exclusión de datos imprescindibles ausentes. Bloqueo por reglas, no por rareza. Evaluación separada de observaciones históricas y llamadas controladas.

**Cerrado en esta revisión:** el ejecutor controlado representa una escena de investigación con las operaciones permitidas y un intento de edición prohibida mediante `wiki.edit`. Las llamadas son guionizadas por nosotros, sin LLM ni gasto de API; el portero y las herramientas locales se ejecutan de verdad. El guion se identifica como material propio: permite verificar trabajo legítimo y ausencia de efecto tras el veto, sin atribuirlo al comportamiento de un modelo. El patrón del tablón sobre la caché de paquetes entra en el informe como análisis dentro de la matriz control × fase, no como demostración implementada; solo se monta como segunda escena si sobra tiempo tras cerrar el núcleo y su evaluación. **La política es una sola y es una lista de las llamadas que la tarea autoriza, con denegación por defecto: lo que no está en la lista se bloquea.** No hay escenario estricto y permisivo; esa pareja venía de cuando el eje era el destino y queda retirada. Las cinco llamadas permitidas salen de la tarea reconstruida. De ExploitGym no se toma nada para el código, incluidos encargos, herramientas y pruebas: solo se usa como contexto documental del control existente para la matriz control × fase. El encargo de las pruebas del ejecutor es una tarea de investigación escrita por nosotros. **La tesis del informe, corregida el 12 de septiembre:** no es que no hubiera controles ni registro. Había identidad, transcripciones y perímetro. Lo que no había era nadie leyendo las transcripciones, el registro estaba donde el agente podía reescribirlo, el canal de coordinación no tenía autenticación y la visibilidad terminaba en el escape del sandbox. Ninguno de los controles preguntaba si una llamada encajaba con el encargo autorizado. El portero es además el punto donde debe producirse el registro de quién hizo qué.

**Pendiente de ejecución de la parte 2:** escribir los casos de trabajo legítimo, fijar el parámetro de la regla de capa 2, consultar las versiones de las guías que se citen, implementar, medir y redactar resultados. La implementación del caso con información completa y el acceso a registros de OpenAI quedan fuera del compromiso del hackathon.

Orden del informe: **el control que existe hoy y sus huecos → el caso de referencia y la matriz → qué datos harían falta y qué no podemos ejecutar → el método implementado con la wiki → resultados y límites**. Siempre separando lo que hicimos, lo que asumimos y lo que proponemos.

Las fuentes están en [el documento del sprint](ai-incident-response-sprint.md) y en [hallazgos-exploitgym.md](hallazgos-exploitgym.md). **Antes de escribir una afirmación sobre los incidentes se comprueba su fuente primaria**; un resumen anterior no vale como comprobación.
