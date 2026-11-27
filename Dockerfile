# Imagen del monolito desplegable (model/rrhh_api.py + model/orquestador.py
# + el conector LLM, ver DECISIONES.md D3).
# Publicarlo solo es posible en las condiciones de CONSTITUTION.md R11. El Cerebro de n8n
# (n8n/workflows/03-cerebro-ia.json) también la llama, como su propio Tier 1
# ("ML"), antes de su propio RAG+LLM (Tier 2, "Agentic"); ver n8n/README.md.
#
# Construir y probar localmente (o usar docker-compose.yml, que ya incluye
# el volumen de retroalimentación):
#   docker build -t prebel-rrhh-api .
#   docker run --rm -p 127.0.0.1:5000:5000 prebel-rrhh-api
#   curl -X POST http://localhost:5000/reply -H "Content-Type: application/json" -d "{\"text\":\"cuantas licencias medicas he tomado\"}"
#   (si pruebas con tildes/ñ por curl en Windows, usa un cliente que mande
#   UTF-8 de verdad -- p. ej. python -c "...urllib...": curl -d en
#   PowerShell/cmd puede mandar la codificación local y corromperlas; no es
#   un bug del servicio, se confirmó probando ambos caminos.)
#
# En el servidor: desplegar en la MISMA red privada de Docker que n8n y
# Ollama (p. ej. como otro servicio de Coolify), SIN mapear el puerto a una
# IP pública -- solo n8n debe poder alcanzarlo.
FROM python:3.11-slim

WORKDIR /app

# PyTorch CPU-only primero: la rueda por defecto de PyPI trae CUDA/nvidia/
# triton empaquetados (~5 GB) que nadie usa aquí -- ni el servidor del
# equipo (sin GPU, ver n8n/README.md) ni esta imagen. Instalarlo antes deja
# satisfecho el "torch>=2.2" de requirements.txt, que no vuelve a
# reinstalarlo con la rueda pesada.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY model/ model/

# Pre-descarga y cachea los ~1 GB de modelos preentrenados en la imagen,
# para que el primer POST /reply real no tenga que esperar esa descarga
# (mismo propósito que "python model/entrenar.py" en la máquina del
# desarrollador -- ver MODEL_TRAINING.md).
RUN python model/entrenar.py

ENV RRHH_API_HOST=0.0.0.0
EXPOSE 5000

CMD ["python", "model/rrhh_api.py"]
