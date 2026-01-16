

# 🌱 Optimización de Riego Deficitario Controlado en cultivos Leñosos Mediante Algoritmos de Machine Learning

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange)](https://www.tensorflow.org/)

# 🌱 Plataforma de Predicción de Riego en Cultivos

Este proyecto se centra en la **predicción de riego y la optimización del uso del agua en cultivos de almendro**, combinando técnicas de minería de datos y series temporales con una **aplicación web** que permite a los usuarios entrenar modelos y generar predicciones a partir de sus propios datos.

El proyecto está dividido en **dos partes independientes**, que no dependen entre sí a nivel de ejecución, pero que están conceptualmente relacionadas.

---

## 📘 Parte 1 — Análisis de Datos y Predicción de Riego (Jupyter Notebook)

Esta parte del proyecto ha sido desarrollada en **Jupyter Notebook** y está enfocada en el análisis y la predicción de las necesidades de riego en un cultivo de almendro.

### Descripción general

El trabajo se basa en **datos reales de 2–3 años**, procedentes de:
- Sensores de suelo
- Datos de precipitaciones
- Radiación solar
- Condiciones climáticas (temperatura, humedad, etc.)

### Proceso realizado

En el notebook se lleva a cabo:
- Limpieza y preprocesado de los datos
- Ingeniería de características
- Entrenamiento de distintos algoritmos de minería de datos y modelos de series temporales
- Predicción de las necesidades de riego
- Cálculo de:
  - **Riego óptimo**
  - **Riego deficitario**, reduciendo porcentajes de riego en épocas menos críticas con el objetivo de mejorar la eficiencia en el uso del agua

### Modelos y técnicas utilizadas
- Redes neuronales **LSTM**
- **SARIMA**
- **SARIMAX**
- **VAR (Vector Autoregression)**
- Pipelines de preprocesado y escalado de datos

Esta parte del proyecto es **totalmente independiente** y puede ejecutarse por separado.

---

## 🌐 Parte 2 — Aplicación Web para Entrenamiento y Predicción

La segunda parte del proyecto consiste en una **aplicación web** que traslada todo el trabajo analítico a una **interfaz accesible para el usuario**.

### Funcionalidades

A través de la aplicación web, un usuario puede:
- Subir su propio archivo de datos (siguiendo el formato requerido)
- Entrenar modelos de predicción
- Realizar predicciones sobre nuevos datos
- Visualizar estadísticas y resultados
- Obtener la **cantidad estimada de riego** que debe aplicarse al cultivo

La aplicación web **no depende del notebook para su ejecución**, aunque está construida a partir de los mismos enfoques, modelos y técnicas.

---

## 🧰 Requisitos

### Generales
- **Git** (para clonar el repositorio, no 100% necesario)
- **Docker** 
- **Python 3.10 o superior**

### ⚠️ Requisito importante de memoria
La configuración del proyecto en Docker está pensada para **cargas de trabajo intensivas en memoria**, especialmente durante el entrenamiento de modelos.

➡️ Es **imprescindible** permitir que Docker pueda asignar **al menos 10–12 GB de RAM** a los contenedores desde la configuración de Docker en el sistema anfitrión.  
En caso contrario, el entrenamiento de modelos puede fallar.

---

### Requisitos para Jupyter Notebook
Para ejecutar el notebook es necesario:

Instalación local: 

- Python 3.10+ (se recomienda, puede funcionar con versiones anteriores)
- pip
- Para visualizar/ejecutar el notebook tienes varias opciones:
  - Jupyter Notebook/Lab
  - Extension de Jupyter para VS Code

  
 **Recomendación:**
**Usar google collab, sin necesidad de ninguna instalación.**


---

## 🧪 Stack Tecnológico


| Componente                | Tecnologías                                                                 |
|---------------------------|----------------------------------------------------------------------------|
| Análisis de datos         | Jupyter Notebook, Python 3.9+, Pandas                                       |
| Minería de datos / IA     | TensorFlow / Keras (LSTM), Scikit-learn, Statsmodels (SARIMA, SARIMAX, VAR)         |
| Backend                   | Python, Flask                                                               |
| Persistencia de datos     | PostgreSQL, SQLAlchemy, Alembic, Flask-Migrate                              |
| Aplicación web            | Flask (renderizado y lógica), HTML                                          |
| Contenerización           | Docker, Docker Compose                                                      |
| Preprocesado de datos     | Scikit-learn (pipelines, escalado), Pandas                                  |


---


## ▶️ Cómo usar el proyecto

### 1️⃣ Clonar el repositorio
```bash
git clone https://github.com/rodrigocastroviejo/Edge-Computing-para-Riego-Deficitario-en-Almendros.git
cd Edge-Computing-para-Riego-Deficitario-en-Almendros
```
## 2️⃣ Ejecutar la aplicación web

Acceder a la carpeta de la aplicación Flask:
```bash
cd myflaskapp
```
Construir y levantar los servicios:

```bash
docker-compose up -d
```

Una vez Docker haya construido y levantado los contenedores, la aplicación estará disponible en:

```bash
http://localhost:5000
```
📄 Licencia

Este proyecto está bajo licencia MIT - ver LICENSE para más detalles.

✉️ Contacto

Carlos Cambra - carlos.cambra@ubu.es
Antonia Maiara Marques Do Nascimiento - ammarquesdo@ubu.es
Proyecto vinculado al Grupo de Investigación XYZ
