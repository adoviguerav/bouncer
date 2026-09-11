# Bouncer

Un portero que comprueba las llamadas a herramienta de un agente antes de ejecutarlas, y registra quién hizo qué desde un punto que el agente no puede reescribir. Proyecto para el AI Incident Response Sprint de Apart Research × CeSIA, Track 1.

## Qué es este repositorio ahora mismo

**Documentación y datos. Todavía no hay código.** Antes de escribir nada, leer:

- [PRD](.codex/plans/PRD.md): requisitos P0, criterios de aceptación y alcance cerrado.
- [Diseño del proyecto](docs/proyecto-portero-tool-calls.md): parte 1 el caso OpenAI/Hugging Face, parte 2 la implementación con la wiki.
- [Instrucciones de trabajo](AGENTS.md): reglas de alcance, datos y evaluación.
- [Tareas pendientes](docs/tareas-pendientes.md).

Si el PRD y el diseño se contradicen, comunicarlo y resolverlo con el usuario antes de cambiar el alcance.

## Stack

Programa local en **Python**. Política en **YAML**, entradas y salidas en **JSONL**. Sin servicios, sin base de datos, sin web, sin plataforma de observabilidad.

Los datos son ficheros comprimidos en `data/collusion-wiki/`. Son 14.591 filas: `gzip` y `json` de la biblioteca estándar bastan, no hace falta pandas ni ninguna dependencia.

Para código del núcleo, pruebas primero y RED-GREEN-IMPROVE, con al menos un 80 % de cobertura. La cobertura no sustituye comprobar efectos e identidad.

## Lo que este proyecto no es

Las reglas y skills que vinieron con la plantilla del repositorio hablan de Next.js, React, Supabase, Tailwind y DaisyUI. **Nada de eso aplica aquí.** Ignorarlas.

## Reglas propias

Se cargan por `@imports` según se vayan añadiendo bajo `.claude/rules/`. Ahora mismo no hay ninguna propia de este proyecto.

## Notas personales (opcional)

Para notas de trabajo o rutas locales que no deben subirse, copiar `CLAUDE.local.md.example` a `CLAUDE.local.md`. Está en gitignore.
