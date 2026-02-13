

# 🌱 Optimización de Riego Deficitario Controlado en cultivos Leñosos Mediante Algoritmos de Machine Learning

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange)](https://www.tensorflow.org/)

# 🌱 Plataforma de Predicción de Riego en Cultivos

Este proyecto se centra en la **predicción de riego y la optimización del uso del agua en cultivos de almendro**, combinando técnicas de minería de datos y series temporales con una **aplicación web** que permite a los usuarios entrenar modelos y generar predicciones a partir de sus propios datos.

El proyecto está dividido en **dos partes independientes**, que no dependen entre sí a nivel de ejecución, pero que están conceptualmente relacionadas.

---

## Parte 1 — Análisis de Datos y Predicción de Riego (Jupyter Notebook)

Esta parte del proyecto ha sido desarrollada en **Jupyter Notebook** y está enfocada en el análisis y la predicción de las necesidades de riego en un cultivo de almendro.

### Descripción general

El trabajo se basa en **datos reales de 2–3 años**, procedentes de:
- Sensores de suelo
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

## Parte 2 — Aplicación Web para Entrenamiento y Predicción

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

## Stack Tecnológico


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

## Guía de Ejecución y Despliegue
[!CAUTION]
**Advertencia sobre el almacenamiento:** El repositorio no incluye los modelos preentrenados por defecto. Tras el entrenamiento, el peso del proyecto puede superar los 25GB. Sin estos modelos, el peso es inferior a 100MB.

### Parte 1: Jupyter Notebook (Análisis y Modelado)
Este componente permite la experimentación, el entrenamiento intensivo y el análisis EDA de forma independiente.

#### A. Ejecución en la Nube (Ready-to-use)
Si no deseas configurar un entorno local, puedes acceder a la versión desplegada:

🌐 Enlace servidor web Jupyter notebook: https://jupyter-notebook.optimizacion-riego-deficitario-controlado-almendro.org

#### B. Ejecución Local (Recomendado para entrenamiento)
Ideal si dispones de hardware potente (GPU) para acelerar las predicciones y re-entrenamientos.

##### Requisitos: 
Tener instalado el Kernel de Jupyter mediante Anaconda o la extensión de VS Code.
##### Preparación: 
Asegúrate de que la carpeta raíz o la carpeta model estén íntegras (el archivo EDA.ipynb depende de loader.py).
##### Ejecución: 
Abre model/EDA.ipynb y selecciona "Ejecutar todo".

Nota: Tiempos de 30 minutos o más son normales debido a la carga computacional.

#### C. Ejecución Local mediante Docker

Para levantar el entorno sin configurar dependencias de Python


Una vez dentro de la carpeta raiz del repositorio clonado de GitHub:

```Bash
cd model 
```

```Bash
docker-compose up -d
```

📍 Acceso: http://localhost:8888

### Parte 2: Aplicación Web (Interfaz de Usuario)


#### A. Ejecución en el servidor

Accede directamente a la aplicación operativa:

🌐 Enlace: https://dash.optimizacion-riego-deficitario-controlado-almendro.org

#### B. Ejecución Local con Docker

##### Requisitos: 
Docker Desktop en funcionamiento y un navegador actualizado.

##### Configuración de Memoria:

 Es imprescindible asignar al menos 10–12 GB de RAM a Docker en la configuración de tu sistema anfitrión para evitar fallos en el entrenamiento.

##### Despliegue:

```Bash
cd myflaskapp
```

```Bash
docker-compose up -d
```

📍 Acceso: http://localhost:5000

### 🛠️ Mantenimiento y Depuración
#### Reseteo de la Base de Datos

Si necesitas limpiar el entorno y reiniciar la estructura de datos desde cero, sigue estos pasos:

##### Eliminar volúmenes de Docker:

Detén los servicios y elimina los volúmenes persistentes de PostgreSQL:

```Bash
docker-compose down -v
```

##### Generar nueva migración (Flask-Migrate):

##### Acceder al contenedor de la app

```Bash
docker exec -it <nombre_contenedor_flask> bash
```

##### Ejecutar comandos de migración

```Bash
flask db init  # Solo si no existe la carpeta migrations
flask db migrate -m "Reinicio de tablas"
flask db upgrade
```

#### Visualización de Logs (Debugging)

##### Identifica el nombre del contenedor:

```Bash
docker ps
```

##### Visualiza los registros:

```Bash
docker logs -f <nombre_del_contenedor_backend>
```




📄 Licencia

Este proyecto está bajo licencia MIT - ver LICENSE para más detalles.

✉️ Contacto

Carlos Cambra - carlos.cambra@ubu.es
Antonia Maiara Marques Do Nascimiento - ammarquesdo@ubu.es
Proyecto vinculado al Grupo de Investigación XYZ

