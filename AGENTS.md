# Instrucciones de trabajo — Bouncer

## Fuentes de alcance

- [PRD](.codex/plans/PRD.md): requisitos, alcance y criterios de aceptación.
- [Diseño del proyecto](docs/proyecto-portero-tool-calls.md): decisiones acordadas, esquema, datos, método y límites de las partes A y B.
- [Documento del sprint](docs/ai-incident-response-sprint.md): contexto y requisitos de la entrega.
- [Hallazgos sobre ExploitGym](docs/hallazgos-exploitgym.md): los tres controles del harness del caso, sus versiones, sus fuentes y su aviso de versión.
- [Hallazgos de METR y Redwood](docs/hallazgos-metr-redwood.md): el tablón sobre la caché de paquetes, las cifras y las transcripciones falseadas. Fuentes secundarias.
- [Tareas pendientes](docs/tareas-pendientes.md).

El diseño sustituye decisiones incompatibles de documentos históricos. Si aparece una contradicción entre el PRD y el diseño, comunicarla y resolverla con el usuario antes de cambiar el alcance. No usar plantillas ni instrucciones de otros agentes como especificación activa por defecto.

## Principios de trabajo

- Usar el especialista adecuado para trabajo sustancial o revisable de forma independiente. Delegar en paralelo exploración, pruebas y revisión independientes; mantener juntas las tareas simples o que modifican los mismos archivos.
- Las decisiones reales de diseño, alcance o compromiso corresponden al usuario. Pedir su razonamiento antes de recomendar; ejecutar directamente el trabajo mecánico ya autorizado. No reabrir decisiones cerradas sin evidencia nueva.
- Antes de una implementación compleja, concretar restricciones, resultado observable, riesgos y verificación. Elegir la solución más pequeña que cumpla el alcance; evitar abstracciones y dependencias especulativas.
- Para código de producción, escribir pruebas significativas primero y seguir RED–GREEN–IMPROVE. Ejecutar las comprobaciones apropiadas y aspirar a una cobertura del núcleo de al menos el 80 %, sin confundir cobertura con corrección. Para experimentos o notebooks, ejecutar y verificar los resultados relevantes.
- Revisar el código modificado con un especialista. Escalar hallazgos materiales de seguridad a `security-reviewer`.
- No exponer, incrustar ni editar secretos sin necesidad. Validar las entradas en los límites de confianza. No ejecutar el contenido del corpus.
- Hacer cambios quirúrgicos, conservar el estilo local y usar identificadores en inglés. No revertir cambios ajenos, silenciar errores ni mutar estado compartido sin control explícito.
- Documentar lo implementado y probado con evidencia. No presentar resultados pendientes, componentes dibujados o propuestas como funcionalidad disponible.

## Alcance cerrado

- Orden de la entrega: primero la **parte 1**, el caso de referencia OpenAI/Hugging Face, y después la **parte 2**, la implementación con la wiki. Lo que ediciones anteriores llamaban parte A es ahora la parte 2, y la parte B es la parte 1.
- Presupuesto de la parte 2: unas 12 horas. Implementar con la wiki un programa local con política YAML y entradas/salidas JSONL.
- Capas obligatorias: **1, permisos explícitos**, y **2, reglas sencillas con memoria por ID**. Incluyen registro de decisiones y prueba del veto con un ejecutor controlado.
- Capas opcionales: **3, revisión con modelo**, y **4, análisis colectivo**. El análisis individual y colectivo reúnen señales en paralelo lógico; no requieren servicios concurrentes. Priorizar núcleo y evaluación antes de extensiones.
- No implementar estadística de rareza, transiciones aprendidas, z-scores ni decaimiento como requisitos. Una rareza no justifica por sí sola bloquear; cada bloqueo necesita un criterio explícito.
- La parte 1, con información completa del operador, queda definida para después. No presupone acceso a datos privados ni entra en la implementación del hackathon. Sí produce ahora un artefacto evaluable: la matriz control × fase de ataque (P0-10).
- No ejecutar ExploitGym. Exige infraestructura de evaluación de capacidad peligrosa y no cabe en el presupuesto. Sus instancias se usan solo como encargo autorizado de pruebas propias, y sus llamadas las escribimos nosotros y se declaran como tales.
- Crear o actualizar documentación no autoriza por sí solo iniciar implementación, publicar ni desplegar.

## Datos y evaluación

- Mantener intactos los archivos originales. Usar `label` literal como ID experimental; excluir los tres nombres humanos identificados. No agrupar por IP, semejanza de texto ni atribuir todas las ediciones anónimas al mismo agente.
- Para cada cálculo, recuperar campos imprescindibles ausentes solo mediante referencias explícitas y no ambiguas; si no es posible, excluir el registro de ese cálculo y registrar el motivo. No descartar datos útiles por campos opcionales ausentes.
- Conservar procedencia, conteos de limpieza y distinción entre campos observados y asignados. `wiki.edit` es una adaptación, no la llamada original recuperada. Un ID de reproducción no es el ID histórico del ejecutor.
- `body` puede conservar texto anterior; no atribuirlo entero al último editor. Una URL citada no prueba una visita. Respetar la incertidumbre de eventos con el mismo segundo y no usar información futura en decisiones cronológicas.
- Reservar `page_family` y sus derivados para evaluación, nunca para reglas o señales. Etiquetas desconocidas no son negativos benignos; función de página no equivale a autorización de una llamada.
- Los datos de Hugging Face son agregados y muestras. No reconstruir una supuesta traza original interpolando eventos, IDs o tiempos. En la matriz control × fase, expresar posiciones como fracciones de la campaña documentada, nunca como números de acción, y declarar el supuesto de encargo del que depende la clasificación.
- Las allowlist de los dos escenarios se toman de la configuración publicada del harness, citando el commit consultado. No inferir una especificación de tarea cuando existe una política publicada.
- No atribuir a la comprobación en la llamada un disparo más temprano que el del perímetro. El reconocimiento inicial está dentro de la forma de una tarea de desarrollo de exploits; su aportación es cobertura, no precocidad.
- Que los agentes de la wiki llegaran por un canal que el control no gobernaba es una hipótesis consistente, no un mecanismo demostrado. El corpus no contiene llamadas a herramienta. Falta el grupo de control de trabajo correcto; los casos propios deben identificarse como tales.
- Registrar siempre qué acción se comprobó y qué identidad la produjo, desde código de confianza. Es la segunda función del portero, no un detalle de implementación.
- Comparar permisos solos con permisos y memoria. Medir efectos impedidos en pruebas controladas, tareas legítimas completadas, bloqueos erróneos, avisos, retenciones y coste, con cantidades y denominadores.
- Verificar que un bloqueo evita invocar la herramienta, que la memoria queda separada por ID y que los límites resisten intentos simultáneos. IDs y políticas vienen del ejecutor de confianza; los argumentos del agente no pueden sustituirlos.
- Separar decisiones retrospectivas sobre la wiki de la prueba de ejecución real. No afirmar prevención del incidente completo ni inventar cómo habría reaccionado un agente tras un bloqueo.
