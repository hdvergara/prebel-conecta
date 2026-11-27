"""Lo que una máquina puede comprobar de la cohesión documental (CONSTITUTION.md
R13). Las contradicciones por transitividad conceptual (R0) no se detectan
aquí: lo que sí se hace es obligar a revisarlas cuando cambia una regla o
quién se apoya en ella.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
EXTENSIONES = {".md", ".py", ".js", ".cjs", ".json", ".yml", ".yaml", ".ps1"}
# Borradores locales, ignorados por git: nada versionado puede citarlos.
# Se arman por partes para que este archivo no se cite a sí mismo.
BORRADORES = [nombre + ".md" for nombre in
              ("ANALISIS_" + "UNIFICACION", "RESUMEN_" + "UNIFICACION_EQUIPO", "REDUCCION_" + "PRIMARIA_DEL_MODELO")]


def _archivos():
    """Versionados más los nuevos todavía sin confirmar; nunca los ignorados."""
    salida = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=RAIZ, capture_output=True, check=True,
    ).stdout.decode("utf-8")
    rutas = [RAIZ / nombre for nombre in salida.split("\0") if nombre]
    return [r for r in rutas if r.is_file() and (r.suffix in EXTENSIONES or r.name == "Dockerfile")]


def _texto(ruta):
    return ruta.read_text(encoding="utf-8")


def _constitucion():
    return _texto(RAIZ / "CONSTITUTION.md")


def test_relative_markdown_links_point_to_existing_files():
    """Given every markdown file in the repository.
    When its relative links are followed.
    Then each one points to a file or folder that exists."""
    rotos = []
    for ruta in _archivos():
        if ruta.suffix != ".md":
            continue
        for destino in re.findall(r"\]\(([^)\s]+)\)", _texto(ruta)):
            if re.match(r"[a-z]+:|#", destino):
                continue
            if not (ruta.parent / destino.split("#")[0]).exists():
                rotos.append(f"{ruta.relative_to(RAIZ)} -> {destino}")
    assert rotos == []


def test_no_versioned_file_cites_an_unversioned_draft():
    """Given the local analysis drafts, which git ignores.
    When the repository is searched.
    Then no file cites them: a reader of the repo could not open them."""
    citas = [f"{ruta.relative_to(RAIZ)} cita {nombre}"
             for ruta in _archivos() for nombre in BORRADORES if nombre in _texto(ruta)]
    assert citas == []


def test_every_cited_rule_id_exists_in_the_constitution():
    """Given the rule IDs defined as headings in CONSTITUTION.md.
    When docs and code cite a rule.
    Then that ID is defined."""
    definidas = set(re.findall(r"^### (R\d+) ", _constitucion(), re.MULTILINE))
    sin_definir = {regla: citan for regla, citan in _citas().items() if regla not in definidas}
    assert sin_definir == {}


# No cuentan como citas: la constitución, la matriz (que recorre reglas para
# revisarlas), el propio registro y el lock de npm (hashes que parecen IDs).
NO_SON_CITAS = {"CONSTITUTION.md", "DECISIONES.md", "tests/trazabilidad.json", "e2e/package-lock.json"}
REGISTRO = RAIZ / "tests" / "trazabilidad.json"


def _citas():
    citas = {}
    for ruta in _archivos():
        nombre = ruta.relative_to(RAIZ).as_posix()
        if nombre not in NO_SON_CITAS:
            for regla in set(re.findall(r"\bR\d{1,2}\b", _texto(ruta))):
                citas.setdefault(regla, set()).add(nombre)
    return {regla: sorted(archivos) for regla, archivos in citas.items()}


def _huella(texto):
    """Insensible a saltos de línea y a cómo esté partido el párrafo."""
    return hashlib.sha256(" ".join(texto.split()).encode("utf-8")).hexdigest()[:16]


def _estado_actual():
    constitucion = _constitucion()
    # Los principios de §0 (presunción, precedencia, términos) también son
    # eslabones de una cadena: cambiarlos obliga a revisar igual que una regla.
    estado = {"§0": {"huella": _huella(constitucion.split("## 1. Spec")[0]), "citan": []}}
    citas = _citas()
    for bloque in re.finditer(r"^### (R\d+) .*?(?=^##|\Z)", constitucion, re.MULTILINE | re.DOTALL):
        estado[bloque[1]] = {"huella": _huella(bloque[0]), "citan": citas.get(bloque[1], [])}
    return estado


def test_a_change_to_a_rule_or_to_who_relies_on_it_forces_the_r0_review():
    """Given tests/trazabilidad.json, the state last reviewed under R0.
    When a rule's text, or the set of files citing it, differs from it.
    Then this fails and names what to review: a rule that still exists can
    stop supporting what a file relies on, which the existence check above
    cannot see."""
    revisado = json.loads(REGISTRO.read_text(encoding="utf-8"))
    actual = _estado_actual()
    pendientes = {
        regla: {"revisado": revisado.get(regla), "actual": actual.get(regla)}
        for regla in sorted(set(revisado) | set(actual))
        if revisado.get(regla) != actual.get(regla)
    }
    assert not pendientes, (
        "Aplica el procedimiento de R0 a estas reglas (cadenas, citas y matriz de DECISIONES.md) "
        "y solo después actualiza tests/trazabilidad.json:\n"
        + json.dumps(pendientes, ensure_ascii=False, indent=2)
    )


def test_every_known_gap_is_tracked_as_an_open_requirement():
    """Given the gaps listed in FLUJOS.md and the open requirements list.
    When their gap IDs are compared.
    Then they match: no gap goes untracked and none is tracked that no longer
    exists."""
    brechas = set(re.findall(r"^\| (B\d+) \|", _texto(RAIZ / "FLUJOS.md"), re.MULTILINE))
    seguidas = set(re.findall(r"^\| RA-\d+ \| (B\d+) \|",
                              _texto(RAIZ / "REQUERIMIENTOS_ABIERTOS.md"), re.MULTILINE))
    assert brechas and brechas == seguidas


def test_the_constitution_holds_no_threshold_values():
    """Given level 0 of the documentation.
    When it is searched for decimal thresholds.
    Then there are none: their only source is model/arquitectura.json."""
    assert re.findall(r"\b0[.,]\d+\b", _constitucion()) == []


def test_flow_document_quotes_the_configured_thresholds():
    """Given the orchestrator thresholds in model/arquitectura.json.
    When FLUJOS.md describes the chain.
    Then it quotes each current value."""
    config = json.loads(_texto(RAIZ / "model" / "arquitectura.json"))
    flujos = _texto(RAIZ / "FLUJOS.md")
    faltan = [clave for clave, valor in config.items()
              if clave.startswith("umbral_") and str(valor) not in flujos]
    assert faltan == []
