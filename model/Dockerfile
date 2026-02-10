# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory to /app
WORKDIR /app

COPY requirements.txt .

# Instalar dependencias 
RUN pip install --no-cache-dir -r requirements.txt

# Install Jupyter Notebok
RUN pip install -no-cache-dir jupyter

# Copy the current directory contents into the container at /app
COPY . .

RUN useradd -m -s /bin/bash rodrigo && \
    chown -R rodrigo:rodrigo /app

USER rodrigo

# Make port 8888 available to the world outside this container
EXPOSE 8080

# Run Jupyter Notebook when the container launches
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8080", "--no-browser"]

# cloudflared tunnel --url http://localhost:8888 --protocol http2