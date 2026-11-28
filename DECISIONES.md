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
| D15 | Sin git, las comprobaciones que necesitan la lista de archivos se saltan con su motivo, sin lista alternativa. Un salto no cuenta como verde | R12 | Vigente. Por confirmar (RA-40) |
| D16 | En el Cerebro de n8n, una respuesta del Nivel 1 que trae un marcador entre corchetes del FAQ ficticio no se usa: la pregunta sigue al Nivel 2, que responde con los documentos reales. El FAQ conserva sus marcadores y no cambia (cierra RA-12). Las entradas sin marcadores que superan el umbral siguen en el Nivel 1 (RA-42) | R1, R5, R8 | Vigente |
| D17 | El repositorio trabaja con especificación primero y diseño guiado por el dominio, sin mover código, en Markdown propio. La carpeta es `especificaciones/` porque `specs/` y `.specs/` guardan documentos reales y git las ignora | R1, R13, R14 | Vigente. El texto de R14 está por confirmar (RA-43) |
| D18 | Los asistentes (Claude, ChatGPT, Codex, Antigravity) comparten una sola fuente, `AGENTS.md`, con adaptadores sin contenido propio. Lo que un asistente puede leer y hacer es una regla (R15), no una instrucción de herramienta | R12, R13, R15 | Vigente. El texto de R15 está por confirmar (RA-46) |
| D19 | Las tareas se derivan de los requerimientos abiertos, uno en exactamente una tarea, sin repetir su texto. Responsables y orden son una propuesta | R13, R14, R15 | Vigente |
| D20 | Las respuestas de Prebel a las preguntas de los equipos (2026-11-28) entran como requerimientos y no cambian ninguna regla. Cada regla se clasifica frente a ellas (ver [Reglas frente a las respuestas de Prebel](#reglas-frente-a-las-respuestas-de-prebel)). El documento original tiene datos reales y queda fuera del repositorio (R1) | R0, R1, R13 | Vigente. Por confirmar (RA-53) |
| D21 | El mecanismo de autenticación o MFA queda como deuda funcional (RA-09). No cambia ni suspende ninguna regla | R7, R11 | Vigente |

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

## Reglas frente a las respuestas de Prebel

Clasificación de D20. Prebel aclaró que las propuestas de los equipos son
decisiones aún no aprobadas por la empresa. Las respuestas se citan por su
número de pregunta, sin copiar el documento.

- **Confirmada:** Prebel pide lo mismo que la regla.
- **Reforzada:** Prebel da una razón de negocio para la regla.
- **En tensión:** la regla se cumple, pero algo que se apoya en ella choca con
  lo que Prebel pide. Se sigue como requerimiento.
- **Interna:** Prebel no la toca.

| Regla | Clase | Respuesta de Prebel | Requerimiento |
|---|---|---|---|
| R7 | Confirmada | 2.3: el número celular por sí solo no basta como autenticación | RA-04, RA-56 |
| R10 | Confirmada | 7.1 y 7.2: precisión, sin inventar, solo con las bases de conocimiento | RA-52, RA-60 |
| R1 | Reforzada | 1.1: los contactos no van incorporados en el código | RA-57 |
| R5 | Reforzada | 1.2, 1.3 y 3.4: horarios, tiempos de respuesta y valores se configuran | RA-58 |
| R8 | Reforzada | 6.3: los documentos se actualizan con RAG, sin reentrenar | -- |
| R9 | Reforzada | 5.4 y 5.5: el modelo se elige al pasar a producción y se usa por API | -- |
| R11 | Reforzada | 6.4: el número de WhatsApp de la empresa se comparte solo tras validar la iniciativa | -- |
| R3, R6, R15 | Reforzada | 5.4: el uso de modelos en la nube se revisa con la empresa | -- |
| R4 | En tensión | 5.1: el asistente indica a quién acudir y no recibe la cédula | RA-54, RA-55 |
| R8 (reuso de la cola) | En tensión | 5.3: en esta fase no se guardan conversaciones | RA-51, RA-59 |
| R0, R2, R12, R13, R14 | Interna | -- | -- |

Ninguna fila cambia el texto de una regla, así que no agrega cadenas a la
matriz. Si resolver RA-51 o RA-54 cambia una regla, se aplica R0.

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
| Pruebas | Salto sin git → "verde" (R12) → trazabilidad (R13) → R0 | Un salto se vería como verde y la protección de R0 desaparecería sin aviso | R12: un salto no cuenta como verde |
| Datos | Lista alternativa sin git → archivos ignorados → R1, R13 (borradores) | Recorrer el disco habría leído documentos reales y borradores locales | No hay lista alternativa |
| Especificaciones, exposición | R14 (especificar antes) → apagar una superficie → R11 | Exigir especificación primero habría demorado apagar una puerta expuesta | Excepción de R14: reducir exposición no espera |
| Especificaciones, documentación | R14 → escenarios → R13 (un hecho, un lugar) → FLUJOS y umbrales | Las especificaciones podían repetir comportamiento y umbrales y quedar distintas | Citan reglas y enlazan comportamiento; una prueba prohíbe umbrales |
| Especificaciones, datos | Carpeta de especificaciones → `specs/` → R1 | La carpeta habitual es la de documentos reales, ignorada por git | Se usa `especificaciones/` |
| Especificaciones, pruebas | R14 (evidencia) → n8n sin pruebas automáticas → R12 | Exigir prueba automática habría impedido todo cambio en n8n | La evidencia puede ser un requerimiento cuyo cierre registra la comprobación manual |
| Especificaciones, autoridad | Escenario → permiso implícito → R0, R10, R11 | Un escenario podía leerse como permiso | R14: un escenario no permite lo que una regla prohíbe |
| Asistentes, datos | R1 (protege el repositorio) → asistente lee `.specs/` → proveedor del modelo → presunción | Los documentos reales podían salir de la máquina sin tocar el repositorio | R15 reserva esas fuentes |
| Asistentes, autoridad | Instrumento → "no abras" → nivel sin reglas → R13 | La prohibición habría sido una regla escrita en un archivo que no puede crearlas | Es R15; los instrumentos la citan |
| Asistentes, secretos | Excepción de R15 (autorizar lectura) → `.env` → R6 | La excepción podía alcanzar los secretos | La excepción nunca cubre secretos ni permite publicar el contenido |
| Asistentes, exposición | R15 (no cambia superficies sin que se lo pidan) → R14 (reducir exposición no espera) → R11 | Podía leerse como freno a apagar una puerta | Limita al asistente por iniciativa propia; si la persona lo pide, actúa sin esperar especificación |
| Asistentes, verificación | ChatGPT sin ejecución → "terminado" → R12 | Un asistente que no ejecuta podía dar algo por verificado | Su texto prohíbe afirmarlo; R12 verifica fuera |
| Tareas | Tarea "Lista" → permiso para ejecutarla → R15 y R11 | Un asistente podía leer una tarea lista como autorización | Las tareas no autorizan nada y "Lista" no significa aprobada |
| Tareas, documentación | Tareas → requerimientos → R13 (un hecho, un lugar) | La tarea podía repetir el requerimiento y su cierre y quedar distinta | La tarea cita IDs. La prueba comprueba la cobertura, no la repetición: eso se revisa |
| Tareas, exposición | Orden por olas → especificar primero (R14) → apagar una puerta (R11) | El plan podía hacer esperar una reducción de exposición | La ola 0 va primero y reducir exposición no espera |
| Niveles | Orden de la tabla de niveles (§0) → "cada nivel se apoya en los de arriba" → las tareas se derivan de los requerimientos abiertos | Las tareas quedaban encima de aquello en lo que se apoyan | Su fila va al final de la tabla |
| Tareas, especificación | Texto del plan → "primero la especificación" → R14 permite el mismo PR | El plan exigía más que la regla: creaba una | El plan repite la condición de R14 |
| Tareas, cierre | Cerrar un requerimiento → la prueba exige editar las tareas → "las tareas no crean nada" | El cierre tenía un paso que su procedimiento no decía | El paso está en el procedimiento de cierre de los requerimientos |
| Especificación, tareas | Escenario con evidencia en una decisión → se cierra la decisión → R14 exige prueba o comprobación manual | El escenario de las puertas quedaba sin evidencia válida | Un escenario por puerta, con evidencia en la brecha que lo aplica |
| Tareas, exposición | TAR-16 "reproducir antes de corregir" → orden de olas → reducir exposición no espera | Reproducir podía frenar una corrección o pedir reactivar puertas | Se reproduce en condiciones controladas y corregir no espera |
| Identidad, deuda | Autenticación como deuda funcional → "puede esperar" → una puerta o un dato sensible sin verificar → R11 y R7 | Aplazar el mecanismo podía leerse como permiso para activar sin él | La deuda no suspende reglas: lo no controlado sigue sin alcanzar ninguna superficie y la identificación básica no se amplía |
| Puente local, configuración | Configuración a voluntad de cada colaborador → abrir la escucha o dejar el secreto público → R11 | La libertad de configurar podía leerse como permiso para dejar el puente al alcance de cualquiera | Cada quien configura y prueba su entorno; eso no suspende R11 |
| Pruebas | `tests/*.cjs` fuera de las suites → R12 → `DEMO.md` | Una guía remitía a pruebas que no cuentan para dar algo por terminado | Se registra en RA-49; no se cambia R12 |
| Portal | R11 → R2 | Sin superficie pública, el recuadro del modelo no responde en una copia publicada | Lo permite R2: el portal funciona sin backend |
| Pruebas | R12 → R2 | Las pruebas de extremo a extremo no podían depender del backend | Interceptan toda llamada a la API |
