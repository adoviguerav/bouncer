# Estructura de proyecto backend de IA (FastAPI + LangGraph + RAG)

Organización por dominio con capa de IA explícita. Regla de dependencia en una sola dirección: `router → service → agents/rag → llm`. Nunca al revés.

## Arquitectura

```
proyecto/
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── data/                        # datos locales, gitignoreada
│   ├── raw/                     # corpus original tal cual llega
│   └── processed/               # intermedio regenerable (limpio, troceado)
├── alembic/                     # migraciones
├── src/
│   ├── main.py                  # crea la app, monta routers, lifespan
│   ├── config.py                # settings globales (pydantic-settings)
│   ├── database.py              # engine, sesiones
│   ├── exceptions.py            # excepciones base
│   │
│   ├── auth/                    # un paquete por dominio de negocio
│   │   ├── router.py
│   │   ├── schemas.py           # modelos pydantic (API)
│   │   ├── models.py            # modelos de BD
│   │   ├── service.py           # lógica de negocio
│   │   ├── dependencies.py
│   │   └── exceptions.py
│   │
│   ├── consultas/               # ejemplo: dominio principal
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── models.py
│   │   ├── service.py           # orquesta: llama a agents/, no al revés
│   │   └── dependencies.py
│   │
│   ├── llm/                     # abstracción del proveedor
│   │   ├── client.py            # interfaz única (chat, embed)
│   │   ├── providers/           # anthropic.py, openai.py, local.py
│   │   ├── config.py            # modelos, temperaturas, fallbacks
│   │   └── prompts/             # prompts versionados como ficheros
│   │       └── triaje_v2.md
│   │
│   ├── agents/                  # grafos LangGraph
│   │   └── triaje/
│   │       ├── graph.py         # construcción del grafo
│   │       ├── state.py
│   │       ├── nodes.py
│   │       └── tools.py
│   │
│   ├── rag/
│   │   ├── ingestion/           # loaders, chunking, embedding
│   │   ├── retrieval/           # búsqueda, reranking, ensamblado
│   │   └── vectorstore.py
│   │
│   └── evals/                   # evaluación desde el día 1
│       ├── datasets/
│       └── run_evals.py
│
└── tests/                       # espeja src/
    ├── consultas/
    └── agents/
```

## Modelo mental: cómo se divide la codebase

En `src/` hay tres niveles:

1. **Lo global** (raíz de src/): `main.py`, `config.py`, `database.py`, `exceptions.py`. Cosas que todo el proyecto usa.
2. **Las piezas** (capacidades horizontales): `llm/`, `rag/`, `agents/`, `evals/`. Funcionalidades que montas una vez y que no saben nada del negocio. Responden a "¿con qué lo hace el producto?"
3. **Los dominios** (verticales de negocio): `auth/`, `consultas/`... Cada uno es una feature con su código propio, y su `service.py` es el punto donde se combinan las piezas: llama a la BD, al LLM, al agente que toque. Responden a "¿qué hace el producto?"

La regla de oro es la dirección de dependencia: los dominios usan las piezas, las piezas nunca conocen a los dominios. Con `agents/` hay un matiz: es pieza y usuaria de piezas a la vez — el dominio llama al agente, y el agente por dentro llama a `llm/` y `rag/`. Y no todo necesita agente: si el dominio solo quiere un resumen o una clasificación, llama a `llm/` directo.

```
dominio (service.py)  →  agents/  →  llm/, rag/
                      →  llm/ o rag/ directamente (si no hace falta grafo)
```

Por qué así: trabajas por features, luego el código se agrupa por features. Tocas una feature → tocas una carpeta. Y si un dominio crece o peta mucho, ya tiene sus fronteras claras: extraerlo a un microservicio es cortar por una costura que ya existe.

## Decisiones que importan

- **Dominio arriba, IA como servicio.** `consultas/service.py` decide cuándo invocar el agente; `agents/` no sabe que existe FastAPI. Esto permite testear el grafo sin levantar el servidor y reutilizarlo desde un worker o un CLI.
- **`llm/` es la capa más rentable del proyecto.** Todo lo que toca un modelo pasa por `llm/client.py`. Cambiar de proveedor, añadir fallback o meter tracing (Langfuse) se hace en un sitio, no en veinte.
- **Prompts como ficheros, no strings.** En `llm/prompts/` con versión en el nombre. Los prompts cambian más que el código; incrustados en funciones no se pueden diffear, revisar ni evaluar.
- **Ingestion y retrieval separados en RAG.** Cambiar la estrategia de chunking no debería tocar el endpoint de query. Es el acoplamiento más común y el más caro.
- **`evals/` existe desde el primer commit.** Aunque sea un JSON con 10 casos y un script. Sin eso, cada cambio de prompt o modelo es fe ciega.

Qué evitar:

- Estructura por capas globales (`routers/`, `crud/`, `models/` en la raíz). Funciona hasta el tercer dominio; luego cada feature obliga a tocar cinco carpetas.
- `utils/` genérico: es donde muere el código sin dueño.

Si el proyecto es solo un agente sin API, simplificar: quitar los dominios y dejar `agents/`, `llm/`, `evals/` colgando de `src/`. La estructura completa se justifica cuando hay backend de verdad con varios dominios.

---

# Leyenda: qué es cada archivo

## Raíz del proyecto

**`pyproject.toml`** — La ficha de identidad del proyecto. Dice cómo se llama, qué versión de Python necesita y qué librerías usa (fastapi, langgraph...). Cuando alguien clona el repo y ejecuta `pip install .` o `uv sync`, este archivo es lo que se lee para instalar todo. También guarda config de herramientas como ruff o pytest.

_¿Por qué pyproject y no requirements.txt?_ `requirements.txt` es solo una lista plana de librerías. `pyproject.toml` es el estándar moderno y hace eso y más: nombre y versión del proyecto, versión mínima de Python, dependencias separadas por grupos (producción vs desarrollo, para no instalar pytest en el servidor), y la config de las herramientas en el mismo sitio. Además permite instalar el proyecto como paquete (`pip install -e .`), lo que arregla los problemas de imports entre carpetas. Herramientas como `uv` o `poetry` trabajan sobre él y generan un lockfile con versiones exactas, que garantiza que en producción se instala exactamente lo mismo que en tu máquina. `requirements.txt` vale para un script; para un proyecto serio, pyproject.

**`docker-compose.yml`** — Una receta para levantar todo lo que la app necesita con un solo comando. Típicamente: la API + una base de datos Postgres + quizá un Redis. En vez de instalar Postgres a mano, escribes `docker compose up` y aparece todo funcionando y conectado entre sí.

**`.env.example`** — Una plantilla de las variables secretas que el proyecto necesita (API keys, contraseña de la BD, URLs). No lleva los valores reales, solo los nombres: `ANTHROPIC_API_KEY=`. Cada persona copia este archivo a `.env`, rellena sus claves, y ese `.env` real nunca se sube a git. Así el repo documenta qué secretos hacen falta sin exponer ninguno.

**`data/`** — El corpus del RAG y demás datos locales. No es código, así que no vive en `src/` y en general va _gitignoreada_ (git es para texto que cambia con diffs, no para 500 PDFs). Dos subcarpetas: `raw/` es el corpus tal cual llega (PDFs, HTML, exports) y es sagrado, nunca se modifica; `processed/` es el intermedio (limpiado, troceado) que puedes borrar y regenerar cuando cambies el chunking. `rag/ingestion/` lee de raw, escribe en processed, y el resultado final (los vectores) acaba en el vectorstore. Si puedes reconstruir todo desde raw ejecutando la ingestion, vas bien.

_Matiz de producción:_ esto vale para desarrollo y proyectos pequeños. En un sistema real el corpus vive en object storage (S3, GCS) o llega de una fuente externa, y la ingestion lee de ahí; `data/` es solo tu copia local de trabajo. Si importa versionar el corpus (p. ej. en clínica, saber con qué guías respondía el sistema en marzo), la herramienta es DVC o el versionado del bucket, no git.

_¿Y por qué los datasets de evals sí van en git (`evals/datasets/`)?_ Porque son la excepción: pequeños (casos, no gigas), son parte del contrato del código (definen qué es "funcionar bien") y quieres que cambien versionados junto al prompt que evalúan. Mismo criterio de siempre: lo que cambia junto, vive junto. El dataset de evals cambia con el código; el corpus cambia por su cuenta.

**`alembic/`** — El historial de cambios de la base de datos. Cada vez que añades una tabla o una columna, alembic genera un pequeño script que dice "añade esta columna". Sirve para que la BD de producción se pueda actualizar paso a paso sin romper nada, y para reconstruir la estructura exacta de la BD desde cero.

_¿Por qué se llama así?_ Es el nombre de la librería de migraciones que acompaña a SQLAlchemy. El nombre es un guiño: un alambique (alembic en inglés) transforma sustancias por destilación, y la librería "transforma" tu base de datos de una versión a otra. La carpeta la genera la propia herramienta al ejecutar `alembic init`.

## Dentro de src/ (nivel global)

**`main.py`** — La puerta de entrada. Aquí se crea la aplicación FastAPI y se le enchufan las piezas: los routers de cada dominio, los middlewares, y qué hacer al arrancar y al apagar (abrir conexión a la BD, cerrarla). Es un archivo corto; si crece, algo está mal colocado.

**`config.py`** — Un solo objeto con toda la configuración de la app: URL de la base de datos, nombre del modelo de LLM por defecto, si estás en desarrollo o producción. Lee las variables del `.env` y las valida (con pydantic-settings). La gracia: si una variable falta o está mal escrita, la app peta al arrancar con un error claro, no a las 3am en producción.

**`database.py`** — La fontanería de la base de datos. Crea la conexión (el "engine") y define cómo se reparten las sesiones (una sesión = una conversación con la BD para atender una petición). Todos los dominios importan de aquí; nadie crea su propia conexión.

_Matiz importante:_ no es "el servicio de la BD" en el sentido de lógica. Es solo la conexión y nada más. La lógica de qué guardar y cuándo vive en los `service.py` de cada dominio; ellos piden una sesión a `database.py` y la usan. Es como el router wifi de tu casa: da conexión a todos, pero no decide qué hace cada uno con ella.

**`exceptions.py`** — Excepciones personalizadas tuyas. Python te da `ValueError` o `Exception`, pero eso no dice nada de tu negocio. Tú defines `ConsultaNoEncontrada` o `PacienteSinPermiso`, y pasan dos cosas buenas. Una, el código se lee solo: `raise ConsultaNoEncontrada` es más claro que `raise ValueError("not found")`. Dos, puedes registrar en FastAPI un manejador que diga "cualquier excepción que herede de `NotFoundError` → devuelve HTTP 404 automáticamente", y ya no escribes ese if en cada endpoint.

_¿Por qué está dos veces (raíz y dominio)?_ No es repetición, es jerarquía. El de la raíz tiene las clases **base**, genéricas: `NotFoundError`, `PermissionError`. El de cada dominio tiene las **concretas** de ese negocio: `CredencialesInvalidas` en auth, `ConsultaNoEncontrada` en consultas, y heredan de las base. El truco: un solo manejador global para `NotFoundError` cubre automáticamente todas las hijas de todos los dominios. Las bases dan el comportamiento común; las concretas dan el nombre legible en el código de cada dominio.

## Dentro de cada dominio (auth/, consultas/...)

_¿Qué es un dominio?_ Una pieza del **negocio**, no una pieza técnica. Un dominio es un área de lo que tu producto _hace_: autenticación, consultas, pacientes, facturación. La alternativa (a evitar) es organizar por pieza técnica: una carpeta `routers/` con todos los routers, una `models/` con todos los modelos...

La diferencia práctica: si organizas por técnica y quieres añadir la feature "citas", tocas cinco carpetas distintas. Si organizas por dominio, creas una carpeta `citas/` y todo lo de citas vive ahí junto: su router, sus schemas, su lógica. Cuando algo de citas falla, sabes exactamente dónde mirar. Y si el proyecto crece tanto que quieres partirlo en microservicios, cada dominio ya es un candidato natural a servicio independiente.

La idea: todos los dominios tienen los mismos archivos con los mismos nombres. Abres cualquier carpeta y ya sabes dónde está cada cosa.

**`router.py`** — Los endpoints HTTP de ese dominio: "cuando llegue un POST a /consultas, ejecuta esto". En cada endpoint hace tres cosas: declara qué schema valida la entrada, llama al service, y declara qué schema da forma a la salida. No encapsula los modelos de Pydantic, los _usa_. Es la ventanilla: recibe, valida contra el contrato, pasa el trabajo al service, devuelve la respuesta con el formato acordado. Luego en `main.py` se hace `app.include_router(...)` y esos endpoints quedan enchufados a la API — por eso main.py es corto: solo enchufa routers, no define endpoints. Cero lógica de negocio aquí; es la recepción del hotel, no la cocina.

**`schemas.py`** — Los contratos de entrada y salida de la API, escritos como modelos de Pydantic. "Para crear una consulta me tienes que mandar un texto y un paciente_id; yo te devolveré un id, una fecha y un resultado." FastAPI los usa para validar automáticamente lo que llega y documentar la API.

**`models.py`** — Las tablas de la base de datos como clases de Python (SQLAlchemy). Cada clase = una tabla, cada atributo = una columna. Ojo con la confusión clásica: `schemas.py` es lo que viaja por la API, `models.py` es lo que se guarda en la BD. Son cosas distintas aunque a veces se parezcan.

**`service.py`** — El cerebro del dominio. Aquí vive la lógica de verdad: "crear una consulta implica guardarla, lanzar el agente de triaje y notificar". Es el único que habla con la BD y con los agentes. Al estar separado del router, se puede testear sin montar un servidor HTTP.

**`dependencies.py`** — Piezas reutilizables que FastAPI inyecta en los endpoints: "dame el usuario autenticado", "dame una sesión de BD", "verifica que esta consulta existe y pertenece a este usuario". Evita repetir esas comprobaciones en cada endpoint.

## llm/

**`client.py`** — Una interfaz única para hablar con cualquier LLM: un método `chat()` y un `embed()`. El código nunca llama a Anthropic o OpenAI directamente; llama a esto. Es el enchufe universal.

**`providers/`** — Las implementaciones concretas de ese enchufe: `anthropic.py` sabe hablar con la API de Anthropic, `openai.py` con la de OpenAI. Cambiar de proveedor = escribir un archivo aquí, sin tocar nada más.

**`config.py`** — Qué modelo usar para qué tarea, con qué temperatura, y a cuál caer si el primero falla. Centralizado para no tener números mágicos repartidos por el código.

**`prompts/`** — Los prompts como archivos de texto, con versión en el nombre (`triaje_v2.md`). Se editan sin tocar código Python, git muestra exactamente qué cambió entre versiones, y se puede evaluar la v2 contra la v1 con los mismos casos.

## agents/ (un subdirectorio por agente)

**`state.py`** — La memoria de trabajo del grafo: qué datos van pasando de nodo en nodo. Típicamente una clase con campos como "mensajes", "documentos recuperados", "decisión". Cada nodo lee este estado y lo actualiza.

**`nodes.py`** — Los pasos del agente como funciones sueltas. Cada función recibe el estado, hace una cosa (llamar al LLM, buscar en el RAG, decidir algo) y devuelve el estado actualizado. Son las casillas del diagrama de flujo.

**`tools.py`** — Las herramientas que el LLM puede decidir usar por su cuenta: buscar en la BD, llamar a una API externa, hacer un cálculo. La diferencia con los nodos: los nodos los ordenas tú en el grafo; las tools las elige el modelo cuando las necesita.

**`graph.py`** — Donde se dibuja el flujo: qué nodo va después de cuál, y las bifurcaciones ("si la confianza es baja, pide revisión humana; si no, responde"). Junta state, nodes y tools en un agente ejecutable.

## rag/

**`ingestion/`** — Todo lo que pasa _antes_ de cualquier pregunta: leer documentos (loaders), trocearlos (chunking) y convertir cada trozo en vectores (embeddings) para guardarlos. Es un proceso que corres de vez en cuando, no en cada petición.

**`retrieval/`** — Todo lo que pasa _cuando llega una pregunta_: buscar los trozos más parecidos, reordenarlos por relevancia (reranking) y montar el contexto que se le pasa al LLM. Esto sí corre en cada petición.

**`vectorstore.py`** — La conexión con la base de datos de vectores (pgvector, Qdrant...). Igual que `database.py` pero para vectores: un solo sitio donde se configura, todos importan de ahí.

## evals/

**`datasets/`** — Los casos de prueba en ficheros: preguntas con la respuesta esperada, o al menos con criterios de qué es una buena respuesta. Se empieza con 10 casos en un JSON y se añade cada caso real que salga mal.

**`run_evals.py`** — El script que pasa todos esos casos por el sistema y dice cuántos salen bien. Se ejecuta antes y después de cambiar un prompt o un modelo: si el número baja, has roto algo. Es el equivalente a los tests, pero para el comportamiento del LLM, que no es determinista.

## tests/

Espeja `src/`: los tests de `consultas/` van en `tests/consultas/`. La diferencia con evals: los tests comprueban que el _código_ funciona (¿el service guarda bien en la BD?), los evals comprueban que el _modelo_ responde bien. Los tests son pasa/no-pasa; los evals son un porcentaje.

---

## Fuentes

- [fastapi-best-practices (zhanymkanov)](https://github.com/zhanymkanov/fastapi-best-practices) — el patrón base por dominios
- [Project Scaffolding for AI Applications (Usama Nawaz)](https://usamanawaz.com/blog/project-scaffolding-ai-applications-folder-structure) — las adiciones específicas de IA
- [How to Design Python AI Projects That Don't Fall Apart (Decoding AI)](https://www.decodingai.com/p/how-to-design-python-ai-projects)
- [Application structure — LangGraph docs](https://docs.langchain.com/oss/python/langgraph/application-structure)
- [fastapi-langgraph-agent-production-ready-template (wassim249)](https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template) — ejemplo real ensamblado
- [Netflix/dispatch](https://github.com/Netflix/dispatch) — el proyecto de producción del que sale el patrón