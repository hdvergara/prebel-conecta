const catalogo = {
  "areas": [
    {
      "id": "produccion",
      "nombre": "Producción",
      "padre": null
    },
    {
      "id": "admin",
      "nombre": "Administración",
      "padre": null
    },
    {
      "id": "gh",
      "nombre": "Gestión Humana",
      "padre": null
    },
    {
      "id": "nomina",
      "nombre": "Nómina",
      "padre": "gh"
    },
    {
      "id": "contratacion",
      "nombre": "Contratación",
      "padre": "gh"
    },
    {
      "id": "sst",
      "nombre": "Seguridad y Salud en el Trabajo",
      "padre": "gh"
    }
  ],
  "personas": [
    {
      "id": "valentina",
      "nombre": "Valentina Ruiz",
      "cargo": "Analista administrativa",
      "area": "admin",
      "saldo": 12,
      "salario": 3000000,
      "ingreso": "2024-01-08"
    },
    {
      "id": "mateo",
      "nombre": "Mateo Ríos",
      "cargo": "Operario de empaque",
      "area": "produccion",
      "saldo": 8,
      "salario": 2200000,
      "ingreso": "2025-03-03"
    }
  ],
  "recursos": [
    {
      "id": "nomina",
      "titulo": "Nómina",
      "responsable": "nomina",
      "audiencia": null,
      "palabras": "pago salario",
      "contenido": ""
    },
    {
      "id": "certificado",
      "titulo": "Certificados",
      "responsable": "contratacion",
      "audiencia": null,
      "palabras": "contrato constancia",
      "contenido": ""
    },
    {
      "id": "dotacion",
      "titulo": "Reposición de protección personal",
      "responsable": "sst",
      "audiencia": "produccion",
      "palabras": "proteccion seguridad guantes gafas epp dotacion planta",
      "contenido": "Para solicitar el cambio de guantes o gafas, indica el elemento y el turno al responsable de SST de tu línea."
    },
    {
      "id": "ergonomia",
      "titulo": "Ergonomía en oficina",
      "responsable": "sst",
      "audiencia": "admin",
      "palabras": "seguridad ergonomia postura silla escritorio oficina",
      "contenido": "Para pedir una revisión del puesto de trabajo, indica tu sede y el elemento que requiere ajuste al equipo de SST."
    }
  ]
};
