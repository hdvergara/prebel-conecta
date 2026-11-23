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
      "id": "impulso",
      "nombre": "Impulso y Mercadeo",
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
    },
    {
      "id": "bienestar",
      "nombre": "Bienestar y RSE",
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
      "ingreso": "2024-01-08",
      "tipo_documento": "CC",
      "numero_documento": "1000000001",
      "telefono": "+57 300 555 0101",
      "correo": "valentina.ruiz@prebel.test",
      "dias_incapacidad": 0,
      "dias_prima": 45,
      "tipo_nomina": "Administrativa"
    },
    {
      "id": "mateo",
      "nombre": "Mateo Ríos",
      "cargo": "Operario de empaque",
      "area": "produccion",
      "saldo": 8,
      "salario": 2200000,
      "ingreso": "2025-03-03",
      "tipo_documento": "CC",
      "numero_documento": "1000000002",
      "telefono": "+57 300 555 0102",
      "correo": "mateo.rios@prebel.test",
      "dias_incapacidad": 3,
      "dias_prima": 30,
      "tipo_nomina": "Operativa"
    },
    {
      "id": "camila",
      "nombre": "Camila Torres",
      "cargo": "Impulsadora comercial",
      "area": "impulso",
      "saldo": 6,
      "salario": 1800000,
      "ingreso": "2025-06-02",
      "tipo_documento": "PPT",
      "numero_documento": "1000000003",
      "telefono": "+57 300 555 0103",
      "correo": "camila.torres@prebel.test",
      "dias_incapacidad": 0,
      "dias_prima": 20,
      "tipo_nomina": "Impulso y mercadeo"
    },
    {
      "id": "andres",
      "nombre": "Andrés Castro",
      "cargo": "Técnico de mantenimiento",
      "area": "produccion",
      "saldo": 15,
      "salario": 2600000,
      "ingreso": "2023-09-15",
      "tipo_documento": "CE",
      "numero_documento": "1000000004",
      "telefono": "+57 300 555 0104",
      "correo": "andres.castro@prebel.test",
      "dias_incapacidad": 1,
      "dias_prima": 60,
      "tipo_nomina": "Operativa"
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
