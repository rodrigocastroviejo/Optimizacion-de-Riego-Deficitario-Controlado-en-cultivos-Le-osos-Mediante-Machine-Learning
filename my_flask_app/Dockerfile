# Imagen base ligera de Python
FROM python:3.10-slim

# Establecer directorio de trabajo
WORKDIR /app

# Evitar que Python genere archivos .pyc y forzar flush de stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias de sistema necesarias (ej: gcc, libpq para Postgres, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Asegurar que Python pueda encontrar los módulos
ENV PYTHONPATH=/app:$PYTHONPATH

# Copiar requirements e instalarlos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Exponer el puerto donde Flask correrá
EXPOSE 5000

# Comando por defecto para correr Flask
# Si usas "run.py" como punto de entrada:
CMD ["python", "run.py"]
