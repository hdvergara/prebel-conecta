#!/usr/bin/env python3
"""Parte los documentos de insumos/ en fichas cortas y genera data/kb.json.

Cada ficha = una sección o una pregunta frecuente de un documento, con su fuente.
No inventa ni resume nada: solo corta, limpia HTML y quita parámetros de rastreo de las URLs.
Uso: python3 -I scripts/ingesta.py   (desde la raíz del proyecto)
Los documentos se leen de insumos/; para usar otra carpeta (por ejemplo .specs/ en el repo del
equipo), define la variable PREBEL_DOCS_DIR. Esa carpeta tiene datos reales: nunca va a git.
"""
import html
import os
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS_DIR = Path(os.environ.get("PREBEL_DOCS_DIR", RAIZ / "insumos"))
# archivo: (nombre, ¿las preguntas frecuentes pertenecen a la sección anterior?)
DOCS = {
    "Auxilios_y_beneficios_Prebel_20260310.md": ("Auxilios y beneficios", False),
    "Creditos_Prebel_20260310.md": ("Créditos", True),
    "Vinculaci_n_y_nomina_20260310.md": ("Vinculación y nómina", True),
    "Glosario_Business_Partner_20260922.md": ("Glosario Business Partner", False),
}
MIN_CHARS = 280     # fichas más cortas se unen a la siguiente de la misma sección
MAX_CHARS = 1600    # fichas más largas se parten por párrafos


def limpiar(texto: str) -> str:
    t = re.sub(r"<br\s*/?>", "\n", texto)
    t = re.sub(r"</(td|th|tr)>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)                       # resto de etiquetas HTML
    t = html.unescape(t)
    t = re.sub(r"([?&])_gl=[^\s)>]*", "", t)            # rastreo de Google
    t = re.sub(r"&origin=lprLink", "", t)
    t = t.replace("\\*", "*").replace("\\_", "_")
    t = re.sub(r"\*\*|__", "", t)                       # negritas
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def es_titulo(linea: str) -> bool:
    l = linea.strip()
    if not l:
        return False
    if l.startswith("#"):
        return True
    if re.fullmatch(r"\*\*[^*]{3,}\*\*:?", l):          # línea completa en negrita
        return True
    if re.match(r"^-\s+\*\*[^*]+\*\*", l):              # término del glosario
        return True
    if re.fullmatch(r"¿[^?]{5,}\?", l):                  # pregunta frecuente sin negrita
        return True
    return False


def nombre_titulo(linea: str) -> str:
    l = linea.strip().lstrip("#").strip().lstrip("-").strip()
    l = l.replace("\\", "")
    m = re.match(r"\*\*([^*]+)\*\*", l)
    if m:
        l = m.group(1)
    return l.strip().rstrip(":").strip()


def es_pregunta(t: str) -> bool:
    return t.startswith("¿")


def es_subtitulo(t: str, padre: str) -> bool:
    """En Vinculación: '3.1 Personal operativo', 'Hijo(s)', 'Si perteneces a…' cuelgan del trámite numerado."""
    if not re.match(r"^\d+\.\s", padre):
        return False
    return bool(re.match(r"^\d+\.\d+", t)) or not re.match(r"^\d+\.", t)


def trocear(nombre_archivo: str, nombre_doc: str, preguntas_hijas: bool):
    lineas = (DOCS_DIR / nombre_archivo).read_text(encoding="utf-8").splitlines()
    secciones = []          # (padre, titulo, [lineas])
    padre, titulo, buf = "", nombre_doc, []
    for linea in lineas:
        if linea.strip() == "***":
            if buf:
                secciones.append((padre, titulo, buf))
            padre, titulo, buf = "", "", []
            continue
        if es_titulo(linea):
            if buf and "".join(buf).strip():
                secciones.append((padre, titulo, buf))
            t = nombre_titulo(linea)
            if es_pregunta(t):
                if not preguntas_hijas:
                    padre = ""
                titulo = t
            elif es_subtitulo(t, padre):
                titulo = t
            else:
                padre, titulo = t, t
            buf = [] if not re.match(r"^-\s+\*\*", linea.strip()) else [linea.strip().split("**", 2)[-1].lstrip(":").strip()]
            continue
        buf.append(linea)
    if buf:
        secciones.append((padre, titulo, buf))

    fichas = []
    for padre, titulo, buf in secciones:
        cuerpo = limpiar("\n".join(buf))
        if not cuerpo:
            continue
        seccion = titulo if (not padre or titulo == padre) else f"{padre} › {titulo}"
        fichas.append({"seccion": seccion, "padre": padre, "texto": cuerpo})

    # unir fichas muy cortas con la siguiente de la misma sección padre
    unidas = []
    for f in fichas:
        prev = unidas[-1] if unidas else None
        misma = prev is not None and prev["padre"] == f["padre"] and f["padre"] != ""
        if misma and (len(prev["texto"]) < MIN_CHARS or len(f["texto"]) < MIN_CHARS) \
                and len(prev["texto"]) + len(f["texto"]) <= MAX_CHARS:
            etiqueta = f["seccion"].split(" › ")[-1]
            prev["texto"] = f"{prev['texto']}\n\n{etiqueta}:\n{f['texto']}"
        else:
            unidas.append(dict(f))

    # partir las largas por párrafos
    final = []
    for f in unidas:
        if len(f["texto"]) <= MAX_CHARS:
            final.append(f)
            continue
        parte, n = "", 1
        for parrafo in re.split(r"\n(?=\S)", f["texto"]):
            if parte and len(parte) + len(parrafo) > MAX_CHARS:
                final.append({**f, "seccion": f"{f['seccion']} (parte {n})", "texto": parte.strip()})
                parte, n = "", n + 1
            parte += parrafo + "\n"
        if parte.strip():
            final.append({**f, "seccion": f"{f['seccion']} (parte {n})" if n > 1 else f["seccion"], "texto": parte.strip()})

    for i, f in enumerate(final, 1):
        prefijo = {"Auxilios y beneficios": "aux", "Créditos": "cred", "Vinculación y nómina": "nom", "Glosario Business Partner": "glo"}[nombre_doc]
        f["id"] = f"{prefijo}-{i:02d}"
        f["documento"] = nombre_doc
        f["archivo"] = nombre_archivo
        f.pop("padre", None)
    return final


def main():
    kb = []
    for archivo, (nombre, hijas) in DOCS.items():
        fichas = trocear(archivo, nombre, hijas)
        kb.extend(fichas)
        print(f"{nombre}: {len(fichas)} fichas", file=sys.stderr)
    (RAIZ / "data").mkdir(exist_ok=True)
    (RAIZ / "data" / "kb.json").write_text(json.dumps(kb, ensure_ascii=False, indent=1), encoding="utf-8")
    largos = [len(f["texto"]) for f in kb]
    print(f"Total: {len(kb)} fichas · tamaño min/medio/max: {min(largos)}/{sum(largos)//len(largos)}/{max(largos)} caracteres", file=sys.stderr)


if __name__ == "__main__":
    main()
