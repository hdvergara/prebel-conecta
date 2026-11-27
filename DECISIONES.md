# Decisiones

Registro de por qué las reglas son como son. No crea reglas: las reglas viven en
[`CONSTITUTION.md`](CONSTITUTION.md). Estado posible: **vigente** o
**reemplazada**. Una decisión no se borra; se marca reemplazada.

## Registro

| ID | Decisión | Reglas | Estado |
|---|---|---|---|
| D1 | n8n orquesta la cadena y Python es su primer nivel | -- | Reemplazada por D2 |
| D2 | Python (`model/orquestador.py`) es el motor principal; n8n pasa a ser un canal o un backend secundario. La LLM se alcanza por un conector intercambiable (MCP) | R8, R9 | Vigente |
| D3 | El backend se despliega como un monolito (`Dockerfile` + `docker-compose.yml`); n8n y Ollama quedan fuera | R11 | Vigente |
| D4 | Lo que resuelve el conector se guarda en una cola; nunca entra solo al FAQ y puede reusarse por similitud | R1, R8, R11 | Vigente |
| D5 | El FAQ admite valores ficticios explícitos y marcados como ejemplo; los valores reales quedan fuera del repositorio. El permiso está en espera de confirmación | R1, R5 | Vigente |
| D6 | n8n cumple un solo rol por despliegue, y el texto generado nunca se presenta como FAQ | R10 | Vigente |
| D7 | La API no se publica mientras tenga conector o cola con datos | R3, R11 | Reemplazada por D10 |
| D8 | Precedencia: protección de datos, luego disponibilidad, luego comportamiento de la demo. No resuelve contradicciones (D12): solo dice qué proteger mientras se corrigen | R0 | Vigente |
| D9 | Documentación por niveles, con control de transitividad al cambiar una regla | R13 | Vigente |
| D10 | Presunción agnóstica a los datos: ninguna superficie que responda desde un backend queda al alcance de quien no esté controlado | R3, R7, R11 | Vigente |
| D11 | La transitividad incluye a quienes citan una regla; un cambio en la regla o en sus citas obliga a revisarlos | R0, R5, R13 | Vigente |
| D12 | La salvaguarda de transitividad es una regla (R0): C no puede contradecir a A por transitividad conceptual en B. La precedencia no resuelve contradicciones | R0 | Vigente |
| D13 | Durante el MVP no se restringe el origen de las llamadas a la API desde un navegador: los ambientes no están definidos y operan en forma cruzada. Sin credenciales entre orígenes | R11 | Vigente, mientras dure el MVP |
| D14 | Se aprueba la redacción de la salvaguarda de transitividad (RA-01) y se adopta su ejemplo formal. La derrotabilidad corrige el texto; la jerarquía normativa solo bloquea la ejecución | R0 | Vigente. Los pesos de la jerarquía están por confirmar (RA-37) |

Notas:

- **D7 → D10:** D7 abría la API cuando no había conector ni cola, presumiendo que
  el FAQ era ficticio. Esa presunción no se puede comprobar en un despliegue.
- **D11** nace de un fallo concreto: R5 se redujo al FAQ mientras tres archivos
  se apoyaban en ella para el marcador de la URL del chat. La prueba pasaba
  porque la regla seguía existiendo.

- **D5** no resuelve que una respuesta ficticia tape a la del RAG de n8n cuando
  ambos cubren el mismo tema (ver las brechas en [`FLUJOS.md`](FLUJOS.md)).
- **D6** incluye la obligación de avisar del texto generado. Se agregó al
  redactar la regla porque, sin ella, un solo rol no basta: el canal puede
  recibir texto generado a través de la API.

## Ejemplo formal de R0

Aportado por el equipo (D14), con correcciones menores de redacción. Ilustra la
regla; si difiere de su texto, rige R0.

### Inconsistencia transitiva en sistemas de reglas

Cuando definimos reglas para generar cualquier trabajo con una IA, se espera que
el conjunto de reglas opere en cadena, pero con frecuencia una regla intermedia
puede provocar que dos o más reglas se contradigan. En lógica y diseño de
sistemas, este fenómeno se conoce como **inconsistencia derivada** o
**conflicto normativo indirecto**.

**La estructura del problema.** El fallo ocurre en cuatro pasos lógicos:

1. **Base (A):** se establece una regla fundamental.
2. **Puente (A → B):** de la regla A se deriva una regla operativa B.
3. **Derivación (B → C):** la formulación de B habilita una tercera regla C.
4. **Contradicción (C → ¬A):** la regla C termina negando o invalidando la regla
   original A.

Por transitividad, aplicar A conduce a ¬A; por lo tanto, la regla B es
**condicionalmente inconsistente**. No es falsa por sí misma, pero está mal
delimitada porque sirve de puente para contradecir una o más premisas previas
que sirven de origen. El orden en que estén definidas dentro del conjunto de
reglas es irrelevante: lo que importa es la cadena conceptual entre ellas.

**Ejemplo.**

- **Regla A:** todo usuario tiene derecho a la privacidad total de sus datos.
- **Regla B:** para proteger esa privacidad, el sistema debe registrar quién
  accede a cada archivo (derivada de A).
- **Regla C:** todo registro de actividad del sistema es público para auditoría
  externa (aplicada sobre B).
- **Resultado:** al aplicar B y C, los datos de acceso de los usuarios se
  vuelven públicos, violando directamente la regla A.

**Soluciones formales.** Implican usar dos herramientas lógicas:

- **Derrotabilidad (*defeasible logic*):** se añade una cláusula de excepción a
  la regla intermedia B. Se reformula estableciendo que A implica B, salvo en
  los casos donde esto active C en contra de A.
- **Jerarquía normativa (*lex superior*):** se asigna un peso mayor a la regla
  fundacional A. Si la cadena transitiva genera un choque, la regla A bloquea
  automáticamente la ejecución de C.

## Matriz de transitividad

Procedimiento y principio: R0.

Cadenas revisadas al redactar la versión actual de las reglas. Cada fila es una
cadena A + B contrastada con C. Es una revisión humana: una cadena que no esté
aquí no está revisada.

| Sujeto | Cadena | Conflicto que había | Cómo queda resuelto |
|---|---|---|---|
| Datos | R5 → R1 | La fuente de valores reales para el FAQ era justo la que no se puede publicar | R5: solo marcadores o ejemplos ficticios; lo real queda fuera |
| Datos | R5 → R4 | Un valor ficticio podía pasar por real | R5 exige que la respuesta diga que es un ejemplo |
| Datos | R5 (valores reales fuera) → `catalogo.py` → portal estático → R11 | Un despliegue con valores reales podía publicarlos como archivo estático | R11: lo estático sale solo de archivos versionados |
| API, URLs | R3 → R11 | El cambio de dirección permitía abrir la API a cualquiera | R11: solo en condiciones controladas, tenga los datos que tenga |
| Cola | R8 (reuso) → R11 | Un anónimo podía llenar la cola y otros recibir lo reusado | Quien está fuera de las condiciones controladas no alcanza la API. Páginas en el navegador de un participante: ver la excepción MVP |
| n8n, API | R10 (canal) → R8 → R10 (aviso) | La API puede escalar y devolver texto generado a un canal | El canal avisa o no usa ese texto. **El código aún no lo cumple** |
| n8n, conector | R10 (backend) → R9 | El backend del conector podía llamar otra vez a la API | R10: la entrada de backend nunca llama a la API |
| Tiempos | R8 → R2 | Escalar puede tardar más de lo que el portal espera | Gana R2 como límite aceptado. Perder la respuesta ya calculada queda como brecha |
| Estructura | R9 → R8 | La regla pedía un módulo por nivel y dos niveles comparten uno | R9 separa responsabilidades, no un módulo por nivel |
| Superficies | n8n → puerta Web pública → R11 | La regla anterior solo cubría la API | R11 cubre toda superficie que responde. **El workflow aún no lo cumple** |
| Identidad | Presunción (§0) → R11 → R7 → puertas de WhatsApp | Una lista de teléfonos permitidos parecería control de acceso | R7: identificar no es controlar el acceso. **Las puertas aún no lo cumplen** |
| Identidad | R7 (puente local con datos ficticios) → presunción → R11 | La presunción podía prohibir la identificación básica de la demo local | La presunción decide quién alcanza una superficie; en condiciones controladas sigue valiendo R7 |
| Configuración | R5 (reducida al FAQ) → marcador de la URL del chat → R13 | Tres archivos se apoyaban en una norma que ya ninguna regla tenía | R5 cubre los marcadores en cualquier archivo |
| Contradicción | Precedencia (§0) → R0 | "Gana la clase menor" permitía convivir con una contradicción que R0 prohíbe | La precedencia solo protege mientras se corrige el texto |
| API, navegador | R3 (la dirección local) → CORS de la API → R11 (llamador no controlado) | Una página ajena, abierta en el navegador del operador, puede llamar a la API local, y R11 no admitía excepciones | Excepción MVP de R11 (D13). Riesgo aceptado |
| Control de acceso | Excepción MVP → sesión del participante (cookies) → R11 (control de acceso) | Con credenciales entre orígenes, cualquier página usaría la sesión y el control quedaría sin efecto | La excepción no admite credenciales entre orígenes |
| Cola | Excepción MVP → `seguir` → conector → cola → R8 (reuso) | Una página ajena puede provocar entradas que luego se reusan con otros participantes | Parte del riesgo aceptado; no sale de las condiciones controladas |
| Datos | Excepción MVP → presunción → R11 | La excepción podía justificarse con "son datos de demo" | No depende de los datos: el riesgo se acepta con cualquiera |
| Datos, identidad | Presunción → R7 → puente local | El texto de la presunción no tenía alcance y, sumado a R7, prohibía la demo local | La presunción quedó acotada a quién alcanza una superficie |
| Pendientes | Requerimientos abiertos → R13 (un hecho, un lugar) → brechas de `FLUJOS.md` | La lista podía duplicar las brechas y quedar distinta | La lista enlaza cada brecha por su ID; una prueba exige que coincidan |
| Pendientes | Requerimientos abiertos (sin confirmar) → R5 (permiso) → FAQ | El permiso podía usarse antes de confirmarlo | R5 deja el permiso en espera |
| Pendientes | Lista que "no crea reglas" → regla general de espera en la lista → presunción acotada → R7 | La lista creaba una regla, y esa regla suspendía la acotación y reabría el choque con R7 | La lista no crea reglas; la única espera está escrita en R5 |
| Contradicción | Jerarquía normativa (ejemplo) → R0 ("la precedencia no la resuelve") → D12 | Si la jerarquía resolviera la contradicción, un texto inconsistente quedaría válido | La jerarquía bloquea la ejecución; el texto se corrige por derrotabilidad |
| Contradicción | Jerarquía normativa (A, la fundacional) → orden irrelevante → clases de precedencia (§0) | Si el orden no cuenta, la cadena no dice cuál es la fundacional | El peso lo dan las clases de §0; con peso igual no se ejecuta lo que niega la premisa. **Por confirmar (RA-37)** |
| Tiempos, disponibilidad | Bloqueo por jerarquía → cadena de respuesta → R8 | Bloquear un paso podía dejar al usuario sin respuesta | El paso bloqueado cae como exige R8 |
| Portal | R11 → R2 | Sin superficie pública, el recuadro del modelo no responde en una copia publicada | Lo permite R2: el portal funciona sin backend |
| Pruebas | R12 → R2 | Las pruebas de extremo a extremo no podían depender del backend | Interceptan toda llamada a la API |
