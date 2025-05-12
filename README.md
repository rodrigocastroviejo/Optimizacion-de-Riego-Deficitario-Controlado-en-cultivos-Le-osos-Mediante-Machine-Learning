

# 🌱 Edge Computing para Riego Deficitario en Almendros

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange)](https://www.tensorflow.org/)

Sistema de riego inteligente que combina edge computing con IA para optimizar el consumo de agua en cultivos de almendro superintensivo.

## 🚀 Características principales

- **Predicción en tiempo real** con modelo LSTM ejecutándose en Arduino Edge Control
- **Control automático** de válvulas de riego basado en datos de sensores
- **Dashboard web** para monitoreo remoto
- **Solución sostenible** que reduce hasta un 30% el consumo de agua

## 🔧 Stack tecnológico

| Componente       | Tecnologías                                                                 |
|------------------|----------------------------------------------------------------------------|
| Edge Computing   | Arduino Edge Control, C++, TensorFlow Lite                                 |
| Backend          | Python 3.8, Flask, SQLAlchemy                                              |
| Frontend         | HTML5, Chart.js, Bootstrap                                                 |
| IA               | TensorFlow/Keras, LSTM, Pandas                                             |
| Base de datos    | PostgreSQL (producción), SQLite (desarrollo)                               |

## 📂 Estructura del proyecto
/edge-riego-almendros/
├── firmware/ # Código para Arduino Edge Control
│ ├── main.cpp # Lógica principal
│ └── tflite_model/ # Modelo convertido
├── model/ # Entrenamiento de IA
│ ├── train.ipynb # Notebook de entrenamiento
│ └── dataset.csv # Datos de ejemplo
├── web/ # Aplicación Flask
│ ├── app.py # Backend
│ ├── templates/ # Vistas HTML
│ └── static/ # CSS/JS
├── docs/ # Documentación
└── requirements.txt # Dependencias


## ⚙️ Requisitos

- Arduino Edge Control
- Sensores de humedad y temperatura
- Python 3.8+
- TensorFlow 2.x

## 🛠️ Instalación

1. Clonar repositorio:
```bash
git clone https://github.com/tu-usuario/edge-riego-almendros.git
cd edge-riego-almendros
Instalar dependencias:
bash
pip install -r requirements.txt
Cargar firmware a la placa (requiere Arduino IDE):
bash
cd firmware
platformio run --target upload
Iniciar servidor web:
bash
cd web
flask run
🌍 Dashboard

Accede al panel de control en http://localhost:5000:

Dashboard Preview

🤝 Contribuciones

¡Bienvenidas! Por favor:

Haz fork del proyecto
Crea una rama (git checkout -b feature/nueva-funcionalidad)
Haz commit de tus cambios (git commit -am 'Añade nueva funcionalidad')
Haz push a la rama (git push origin feature/nueva-funcionalidad)
Abre un Pull Request
📄 Licencia

Este proyecto está bajo licencia MIT - ver LICENSE para más detalles.

✉️ Contacto

Carlos Cambra - carlos.cambra@ubu.es
Proyecto vinculado al Grupo de Investigación XYZ
