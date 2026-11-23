"""Construye el catálogo local y exporta los datos ficticios de la demo estática."""
import json
import sqlite3
from pathlib import Path

root = Path(__file__).resolve().parent
empleados = json.loads((root / "model" / "empleados_mock.json").read_text(encoding="utf-8"))["empleados"]

with sqlite3.connect(root / "demo.sqlite3") as db:
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        DROP TABLE IF EXISTS recursos;
        DROP TABLE IF EXISTS personas;
        DROP TABLE IF EXISTS areas;
        CREATE TABLE areas(id TEXT PRIMARY KEY, nombre TEXT NOT NULL, padre TEXT REFERENCES areas);
        CREATE TABLE personas(
            id TEXT PRIMARY KEY, nombre TEXT, cargo TEXT, area TEXT REFERENCES areas,
            saldo INTEGER, salario INTEGER, ingreso TEXT,
            tipo_documento TEXT, numero_documento TEXT, telefono TEXT, correo TEXT,
            dias_incapacidad INTEGER, dias_prima INTEGER, tipo_nomina TEXT
        );
        CREATE TABLE recursos(id TEXT PRIMARY KEY, titulo TEXT, responsable TEXT REFERENCES areas, audiencia TEXT REFERENCES areas, palabras TEXT, contenido TEXT);
    """)
    db.executemany("INSERT INTO areas VALUES(?,?,?)", [
        ("produccion","Producción",None), ("admin","Administración",None), ("impulso","Impulso y Mercadeo",None),
        ("gh","Gestión Humana",None), ("nomina","Nómina","gh"),
        ("contratacion","Contratación","gh"), ("sst","Seguridad y Salud en el Trabajo","gh"),
        ("bienestar","Bienestar y RSE","gh")])
    db.executemany("INSERT INTO personas VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
        (e["id"], e["primer_nombre"] + " " + e["apellido"], e["cargo"], e["area"],
         e["dias_vacaciones_acumulados"], e["salario_actual"], e["fecha_ingreso"],
         e["tipo_documento"], e["numero_documento"], e["telefono"], e["correo"],
         e["dias_incapacidad_reportados"], e["dias_prima_acumulados"], e["tipo_nomina"])
        for e in empleados])
    db.executemany("INSERT INTO recursos VALUES(?,?,?,?,?,?)", [
        ("nomina","Nómina","nomina",None,"pago salario",""),
        ("certificado","Certificados","contratacion",None,"contrato constancia",""),
        ("dotacion","Reposición de protección personal","sst","produccion","proteccion seguridad guantes gafas epp dotacion planta","Para solicitar el cambio de guantes o gafas, indica el elemento y el turno al responsable de SST de tu línea."),
        ("ergonomia","Ergonomía en oficina","sst","admin","seguridad ergonomia postura silla escritorio oficina","Para pedir una revisión del puesto de trabajo, indica tu sede y el elemento que requiere ajuste al equipo de SST.")])
    db.row_factory = sqlite3.Row
    data = {table:[dict(row) for row in db.execute("SELECT * FROM "+table)] for table in ("areas","personas","recursos")}
(root / "dist" / "catalogo.js").write_text("const catalogo = "+json.dumps(data,ensure_ascii=False,indent=2)+";\n",encoding="utf-8")

faq = json.loads((root / "model" / "faq_rrhh.json").read_text(encoding="utf-8"))
(root / "dist" / "faq.js").write_text("const faqModel = "+json.dumps(faq,ensure_ascii=False,indent=2)+";\n",encoding="utf-8")
