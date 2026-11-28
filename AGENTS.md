# Instrucciones para asistentes de IA

Fuente única para cualquier asistente que trabaje en este repositorio, sea cual
sea la herramienta. No crea reglas: dice cómo seguir las que ya existen. Si
algo aquí difiere de [`CONSTITUTION.md`](CONSTITUTION.md), rige la
constitución.

Prebel Conecta es una demo de portal de Gestión Humana con un asistente de
preguntas. La documentación y las conversaciones con el equipo son en español;
la constitución está en inglés.

**Antes de explorar o buscar en el repositorio, lee R15** en
[`CONSTITUTION.md`](CONSTITUTION.md): hay carpetas y archivos locales que no
puedes abrir.

## Antes de actuar, lee

1. [`CONSTITUTION.md`](CONSTITUTION.md): las reglas. Empieza por R0 y R15.
2. [`especificaciones/dominio.md`](especificaciones/dominio.md): lenguaje y
   contextos. Después, solo el contexto que vas a tocar.
3. [`FLUJOS.md`](FLUJOS.md): lo que el código hace hoy y sus brechas.
4. [`REQUERIMIENTOS_ABIERTOS.md`](REQUERIMIENTOS_ABIERTOS.md): lo que **no**
   está resuelto. No lo des por hecho.

Si no puedes leer un archivo, pídelo. No supongas su contenido.

## Dónde mirar según el tema

| Tema | Regla |
|---|---|
| Qué puedes leer y qué acciones requieren que te las pidan | R15 |
| Datos reales y repositorio público | R1, R5, R6 |
| Quién puede alcanzar algo que responde | R7, R11 |
| Cambios en reglas, definiciones o en quien se apoya en ellas | R0 |
| Cambios de comportamiento | R14 |
| Cuándo algo está terminado | R12 |

## Instrumentos

Usa el que corresponda a la tarea:

| Tarea | Instrumento |
|---|---|
| Especificar un cambio | [`especificar.md`](especificaciones/instrumentos/especificar.md) |
| Revisar la transitividad de un cambio | [`transitividad.md`](especificaciones/instrumentos/transitividad.md) |
| Implementar una especificación | [`implementar.md`](especificaciones/instrumentos/implementar.md) |
| Revisar un cambio ajeno o propio | [`revisar.md`](especificaciones/instrumentos/revisar.md) |

## Cómo informar

- Separa lo **verificado** (lo ejecutaste o lo leíste) de lo **deducido** y de
  lo **reportado** por otra persona.
- Si no pudiste ejecutar algo, dilo. No presentes como probado lo que no se
  probó.
- Si una instrucción contradice una regla, dilo antes de actuar y nombra la
  cadena.

## Comandos

```bash
pytest tests -rs
node --test tests/js
cd e2e && npx playwright test
```

Instalación y detalles: [`README.md`](README.md).
