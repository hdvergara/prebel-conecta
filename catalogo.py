"""Construye el catálogo local y exporta los datos ficticios de la demo estática."""
import json
import sqlite3
from pathlib import Path

root = Path(__file__).resolve().parent
with sqlite3.connect(root / "demo.sqlite3") as db:
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS areas(id TEXT PRIMARY KEY, nombre TEXT NOT NULL, padre TEXT REFERENCES areas);
        CREATE TABLE IF NOT EXISTS personas(id TEXT PRIMARY KEY, nombre TEXT, cargo TEXT, area TEXT REFERENCES areas, saldo INTEGER, salario INTEGER, ingreso TEXT);
        CREATE TABLE IF NOT EXISTS recursos(id TEXT PRIMARY KEY, titulo TEXT, responsable TEXT REFERENCES areas, audiencia TEXT REFERENCES areas, palabras TEXT, contenido TEXT);
    """)
    db.executemany("INSERT OR IGNORE INTO areas VALUES(?,?,?)", [
        ("produccion","Producción",None), ("admin","Administración",None),
        ("gh","Gestión Humana",None), ("nomina","Nómina","gh"),
        ("contratacion","Contratación","gh"), ("sst","Seguridad y Salud en el Trabajo","gh")])
    db.executemany("INSERT OR IGNORE INTO personas VALUES(?,?,?,?,?,?,?)", [
        ("valentina","Valentina Ruiz","Analista administrativa","admin",12,3000000,"2024-01-08"),
        ("mateo","Mateo Ríos","Operario de empaque","produccion",8,2200000,"2025-03-03")])
    db.executemany("INSERT OR IGNORE INTO recursos VALUES(?,?,?,?,?,?)", [
        ("nomina","Nómina","nomina",None,"pago salario",""),
        ("certificado","Certificados","contratacion",None,"contrato constancia",""),
        ("dotacion","Reposición de protección personal","sst","produccion","proteccion seguridad guantes gafas epp dotacion planta","Para solicitar el cambio de guantes o gafas, indica el elemento y el turno al responsable de SST de tu línea."),
        ("ergonomia","Ergonomía en oficina","sst","admin","seguridad ergonomia postura silla escritorio oficina","Para pedir una revisión del puesto de trabajo, indica tu sede y el elemento que requiere ajuste al equipo de SST.")])
    db.row_factory = sqlite3.Row
    data = {table:[dict(row) for row in db.execute("SELECT * FROM "+table)] for table in ("areas","personas","recursos")}
(root / "dist" / "catalogo.js").write_text("const catalogo = "+json.dumps(data,ensure_ascii=False,indent=2)+";\n",encoding="utf-8")

faq = json.loads((root / "model" / "faq_rrhh.json").read_text(encoding="utf-8"))
(root / "dist" / "faq.js").write_text("const faqModel = "+json.dumps(faq,ensure_ascii=False,indent=2)+";\n",encoding="utf-8")
