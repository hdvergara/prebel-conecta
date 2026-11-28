"""Lo que una máquina puede comprobar de las especificaciones
(especificaciones/README.md, CONSTITUTION.md R14). No comprueba que una prueba
cubra de verdad lo que dice su escenario. No necesita git.
"""
import ast
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ESPECIFICACIONES = RAIZ / "especificaciones"
CONTEXTOS = {ruta.stem: ruta.read_text(encoding="utf-8")
             for ruta in sorted((ESPECIFICACIONES / "contextos").glob("*.md"))}
# Estado generado en ejecución, ignorado por git: no es un módulo de nadie.
ESTADO_GENERADO = {"retroalimentacion.json"}


def _escenarios():
    for contexto, texto in CONTEXTOS.items():
        for linea in re.findall(r"^\| (ESC-[A-Z]+-\d+) \| .* \| (.+?) \|$", texto, re.MULTILINE):
            yield contexto, linea[0], linea[1].strip().strip("`")


def _modulos():
    """{ruta del archivo de model/: contexto que lo declara en su tabla}."""
    declarados = {}
    for contexto, texto in CONTEXTOS.items():
        for ruta in re.findall(r"^\| `(model/[\w.]+)` \|", texto, re.MULTILINE):
            declarados.setdefault(ruta, []).append(contexto)
    return declarados


def _error_de_evidencia(evidencia, requerimientos):
    if re.fullmatch(r"RA-\d+", evidencia):
        return None if evidencia in requerimientos else "el requerimiento no existe"
    if "::" not in evidencia:
        return "no es una prueba ni un requerimiento"
    archivo, nombre = evidencia.split("::", 1)
    ruta = RAIZ / archivo
    if not ruta.is_file():
        return "el archivo de prueba no existe"
    texto = ruta.read_text(encoding="utf-8")
    patron = (rf"^def {re.escape(nombre)}\(" if ruta.suffix == ".py"
              else rf"""\btest\(\s*(["']){re.escape(nombre)}\1""")
    return None if re.search(patron, texto, re.MULTILINE) else "la prueba no existe en ese archivo"


def test_every_scenario_points_to_existing_evidence():
    """Given the scenarios of every context.
    When their evidence is looked up.
    Then it is a test that exists or a listed requirement."""
    lista = (RAIZ / "REQUERIMIENTOS_ABIERTOS.md").read_text(encoding="utf-8")
    requerimientos = set(re.findall(r"^\| (RA-\d+) \|", lista, re.MULTILINE))
    escenarios = list(_escenarios())
    errores = {id_: f"{evidencia}: {error}" for _, id_, evidencia in escenarios
               if (error := _error_de_evidencia(evidencia, requerimientos))}
    assert escenarios and errores == {}


def test_every_scenario_row_is_read_and_has_a_unique_id():
    """Given every table row that starts with a scenario ID.
    When the rows are parsed.
    Then none is silently skipped for being malformed, and no ID repeats."""
    filas = [id_ for texto in CONTEXTOS.values()
             for id_ in re.findall(r"^\| (ESC-[\w-]+)", texto, re.MULTILINE)]
    assert filas == [id_ for _, id_, _ in _escenarios()]
    assert len(filas) == len(set(filas))


def test_every_model_file_belongs_to_exactly_one_context():
    """Given the Python modules and data files in model/.
    When the context module tables are read.
    Then each file is claimed exactly once, and no table names a missing file."""
    reales = {f"model/{ruta.name}" for ruta in (RAIZ / "model").iterdir()
              if ruta.suffix in {".py", ".json"} and ruta.name not in ESTADO_GENERADO}
    declarados = _modulos()
    assert set(declarados) == reales
    assert {ruta: quien for ruta, quien in declarados.items() if len(quien) != 1} == {}


def test_dependencies_between_contexts_are_the_declared_ones():
    """Given the imports between modules of model/.
    When they are grouped by context.
    Then each context depends on exactly what it declares: a new or removed
    dependency must show up in the specification."""
    dueno = {Path(ruta).stem: quien[0] for ruta, quien in _modulos().items() if ruta.endswith(".py")}
    reales = {contexto: set() for contexto in CONTEXTOS}
    for modulo, contexto in dueno.items():
        arbol = ast.parse((RAIZ / "model" / f"{modulo}.py").read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            nombres = ([a.name for a in nodo.names] if isinstance(nodo, ast.Import)
                       else [nodo.module] if isinstance(nodo, ast.ImportFrom) else [])
            reales[contexto] |= {dueno[n] for n in nombres if n in dueno and dueno[n] != contexto}
    declaradas = {}
    for contexto, texto in CONTEXTOS.items():
        lista = re.search(r"^\*\*Depende de:\*\* (.+)$", texto, re.MULTILINE)[1]
        declaradas[contexto] = set() if lista == "ninguno" else set(lista.split(", "))
    assert reales == declaradas


def test_specifications_hold_no_threshold_values():
    """Given the specification files.
    When searched for decimal thresholds.
    Then there are none: their only source is model/arquitectura.json."""
    con_valores = {ruta.name: valores for ruta in ESPECIFICACIONES.rglob("*.md")
                   if (valores := re.findall(r"\b0[.,]\d+\b", ruta.read_text(encoding="utf-8")))}
    assert con_valores == {}
