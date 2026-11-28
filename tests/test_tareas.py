"""Mantiene especificaciones/TAREAS.md al día con los requerimientos abiertos.
No comprueba que el orden o las dependencias sean acertados. No necesita git.
"""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
FILA = re.compile(r"^\| (TAR-\d+) \| [^|]+ \| ([^|]+) \| [^|]+ \| ([^|]+) \| (Lista|Bloqueada) \|$", re.MULTILINE)


def _lista(celda):
    return [] if celda.strip() == "--" else [parte.strip() for parte in celda.split(",")]


def _tareas():
    texto = (RAIZ / "especificaciones" / "TAREAS.md").read_text(encoding="utf-8")
    return [(id_, _lista(ra), _lista(deps), estado) for id_, ra, deps, estado in FILA.findall(texto)]


def _abiertos():
    texto = (RAIZ / "REQUERIMIENTOS_ABIERTOS.md").read_text(encoding="utf-8")
    assert "\n## Cerrados\n" in texto, "sin esa sección, lo cerrado contaría como abierto"
    return set(re.findall(r"^\| (RA-\d+) \|", texto.split("\n## Cerrados")[0], re.MULTILINE))


def test_every_task_row_is_read_and_has_a_unique_id():
    """Given every row that starts with a task ID in the wave tables.
    When the rows are parsed.
    Then none is silently skipped for being malformed, and no ID repeats."""
    texto = (RAIZ / "especificaciones" / "TAREAS.md").read_text(encoding="utf-8")
    filas = re.findall(r"^\| (TAR-\d+) \|", texto.split("## Puntos de partida")[0], re.MULTILINE)
    assert filas and filas == [id_ for id_, *_ in _tareas()]
    assert len(filas) == len(set(filas))


def test_each_open_requirement_is_in_exactly_one_task():
    """Given the open requirements.
    When the tasks are read.
    Then each open one is in exactly one task, and no task keeps a closed or
    unknown one."""
    asignados = [ra for _, requerimientos, *_ in _tareas() for ra in requerimientos]
    assert sorted(set(asignados)) == sorted(_abiertos())
    assert sorted({ra for ra in asignados if asignados.count(ra) > 1}) == []


def test_dependencies_exist_have_no_cycles_and_match_the_state():
    """Given each task's dependencies.
    When they are followed.
    Then they name existing tasks, never loop, and a task is 'Lista' exactly
    when it depends on nothing."""
    dependencias = {id_: deps for id_, _, deps, _ in _tareas()}
    assert {d for deps in dependencias.values() for d in deps} <= set(dependencias)
    assert [id_ for id_, _, deps, estado in _tareas() if (estado == "Lista") != (not deps)] == []

    def recorrer(id_, camino):
        assert id_ not in camino, f"ciclo: {' -> '.join(camino + [id_])}"
        for siguiente in dependencias[id_]:
            recorrer(siguiente, camino + [id_])

    for id_ in dependencias:
        recorrer(id_, [])


def test_no_task_waits_for_a_later_wave_or_repeats_a_dependency():
    """Given the waves in the order they appear.
    When each task's dependencies are placed in them.
    Then none sits in a later wave, and none is listed twice."""
    texto = (RAIZ / "especificaciones" / "TAREAS.md").read_text(encoding="utf-8")
    ola = {id_: numero for numero, bloque in enumerate(texto.split("## Puntos de partida")[0].split("\n## Ola "))
           for id_, *_ in FILA.findall(bloque)}
    assert [(id_, d) for id_, _, deps, _ in _tareas() for d in deps if ola[d] > ola[id_]] == []
    assert [id_ for id_, _, deps, _ in _tareas() if len(deps) != len(set(deps))] == []


def test_starting_points_name_existing_tasks_and_scenarios():
    """Given the starting points.
    When their task and scenario IDs are looked up.
    Then every one exists."""
    puntos = (RAIZ / "especificaciones" / "TAREAS.md").read_text(encoding="utf-8").split("## Puntos de partida")[1]
    contextos = "".join(ruta.read_text(encoding="utf-8")
                        for ruta in (RAIZ / "especificaciones" / "contextos").glob("*.md"))
    assert set(re.findall(r"TAR-\d+", puntos)) <= {id_ for id_, *_ in _tareas()}
    assert set(re.findall(r"ESC-[A-Z]+-\d+", puntos)) <= set(re.findall(r"^\| (ESC-[A-Z]+-\d+) \|", contextos, re.MULTILINE))
