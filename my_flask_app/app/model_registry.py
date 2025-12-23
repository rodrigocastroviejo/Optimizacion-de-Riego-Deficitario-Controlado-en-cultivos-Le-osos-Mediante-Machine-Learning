# app/model_registry.py
"""
Registro de clases personalizadas para deserialización de modelos.
Esto es necesario porque joblib necesita acceso a las clases originales.
"""

from app.ml_models import SarimaModel, SarimaxModel, VarModel, LSTMModel

# Lista de todas las clases personalizadas que se usan en los modelos
CUSTOM_CLASSES = {
    'SarimaModel': SarimaModel,
    'SarimaxModel': SarimaxModel,
    'VarModel': VarModel,
    'LSTMModel': LSTMModel
}

def register_custom_classes():
    """Esta función no hace nada explícito, pero al importarla
       asegura que las clases estén disponibles en el namespace."""
    pass