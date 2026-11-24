# Imagen del modelo de RRHH (model/rrhh_api.py), para desplegar junto a n8n
# y Ollama en el servidor del equipo -- no para exponer al público. El
# Cerebro de n8n (n8n/workflows/03-cerebro-ia.json) la llama como Tier 1
# ("ML") antes de su propio RAG+LLM (Tier 2, "Agentic"); ver n8n/README.md.
#
# Construir y probar localmente:
#   docker build -t prebel-rrhh-api .
#   docker run --rm -p 5000:5000 prebel-rrhh-api
#   curl -X POST http://localhost:5000/reply -H "Content-Type: application/json" -d "{\"text\":\"¿Cuándo pagan la nómina?\"}"
#
# En el servidor: desplegar en la MISMA red privada de Docker que n8n y
# Ollama (p. ej. como otro servicio de Coolify), SIN mapear el puerto a una
# IP pública -- solo n8n debe poder alcanzarlo.
FROM python:3.11-slim

WORKDIR /app

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
