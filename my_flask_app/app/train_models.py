# train_models.py
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.compose import ColumnTransformer

# Asegurar que las clases personalizadas estén registradas
from app.model_registry import register_custom_classes
register_custom_classes()

from app.ml_models import SarimaModel, SarimaxModel, VarModel, LSTMModel

# =========================
# CONFIGURACIÓN
# =========================
DIR_APP = Path(__file__).resolve().parent
BASE_DIR = DIR_APP.parent

DATA_PATH = BASE_DIR / "uploads" / "datos_entrenamiento_fisico.csv"
MODELS_PATH = DIR_APP / "models"

MODELS_PATH.mkdir(exist_ok=True)

class Config:
    SARIMA_ORDER = (1, 1, 1)
    SARIMA_SEASONAL_ORDER = (1, 1, 1, 30)
    VAR_MAXLAGS = 15
    TEST_SIZE = 180

# =========================
# FUNCIONES AUXILIARES
# =========================
def load_and_prepare_data(path: Path) -> pd.DataFrame:
    """Cargar y preparar datos para entrenamiento"""
    print(f"📂 Cargando datos de: {path}")
    
    df = pd.read_csv(path)
    
    # Detectar columna de fecha
    date_cols = [col for col in df.columns if 'fecha' in col.lower()]
    if date_cols:
        df = pd.read_csv(path, parse_dates=[date_cols[0]], index_col=date_cols[0])
    else:
        df = pd.read_csv(path)
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            df.set_index('Fecha', inplace=True)
        else:
            # Crear índice temporal si no hay fecha
            df.index = pd.date_range(start='2000-01-01', periods=len(df), freq='D')
    
    df = df.sort_index()
    
    # Interpolar valores faltantes
    full_range = pd.date_range(df.index.min(), df.index.max(), freq="D")
    df = df.reindex(full_range)
    df = df.interpolate(method="time")
    
    print(f"✅ Datos cargados: {df.shape[0]} filas, {df.shape[1]} columnas")
    return df

def temporal_train_test_split(df, test_size):
    """Dividir datos en train/test temporalmente"""
    split = len(df) - test_size
    train_df = df.iloc[:split]
    test_df = df.iloc[split:]
    
    print(f"📊 Split temporal: Train={len(train_df)}, Test={len(test_df)}")
    return train_df, test_df

def create_custom_scaler(df):
    """Crear ColumnTransformer para escalado personalizado"""
    # Identificar columnas para cada tipo de escalado
    all_cols = df.columns.tolist()
    
    # Columnas para StandardScaler (distribución normal)
    std_cols = []
    # Columnas para RobustScaler (con outliers)
    robust_cols = []
    
    for col in all_cols:
        if any(x in col.lower() for x in ['velocidad', 'presión', 'precipitacion', 'precipitaciones']):
            robust_cols.append(col)
        else:
            std_cols.append(col)
    
    print(f"🔧 Escalado: Standard={std_cols}, Robust={robust_cols}")
    
    return ColumnTransformer(
        transformers=[
            ("std", StandardScaler(), std_cols),
            ("robust", RobustScaler(), robust_cols),
        ],
        remainder="passthrough",
        verbose_feature_names_out=False,
    ).set_output(transform="pandas")

# =========================
# PIPELINES
# =========================
def create_sarima_pipelines(df):
    """Crear pipelines SARIMA para cada variable"""
    pipelines = {}
    scaler = create_custom_scaler(df)
    
    for col in df.columns:
        print(f"🔄 Creando pipeline SARIMA para: {col}")
        pipeline_name = f"sarima_{col}"
        
        pipelines[pipeline_name] = Pipeline([
            ("scaler", scaler),
            ("sarima", SarimaModel(
                column=col,
                order=Config.SARIMA_ORDER,
                seasonal_order=Config.SARIMA_SEASONAL_ORDER,
            ))
        ])
    
    return pipelines

def create_sarimax_pipelines(df):
    """Crear pipelines SARIMAX para cada variable"""
    pipelines = {}
    scaler = create_custom_scaler(df)
    cols = df.columns.tolist()
    
    for target in cols:
        exog = [c for c in cols if c != target]
        print(f"🔄 Creando pipeline SARIMAX para: {target} (exógenas: {exog[:2]}...)")
        
        pipeline_name = f"sarimax_{target}"
        
        pipelines[pipeline_name] = Pipeline([
            ("scaler", scaler),
            ("sarimax", SarimaxModel(
                target_col=target,
                exog_cols=exog,
                order=Config.SARIMA_ORDER,
                seasonal_order=Config.SARIMA_SEASONAL_ORDER,
            ))
        ])
    
    return pipelines

def create_var_pipeline(df):
    """Crear pipeline VAR multivariante"""
    print("🔄 Creando pipeline VAR multivariante")
    scaler = create_custom_scaler(df)
    
    return Pipeline([
        ("scaler", scaler),
        ("var", VarModel(maxlags=Config.VAR_MAXLAGS)),
    ])

def create_lstm_pipeline(df):
    """Crear pipeline LSTM multivariante"""
    print("🔄 Creando pipeline LSTM multivariante")
    
    scaler = ColumnTransformer([
        ("scaler", MinMaxScaler(feature_range=(0, 1)), df.columns.tolist()),
    ], remainder="passthrough", verbose_feature_names_out=False).set_output(transform="pandas")
    
    return Pipeline([
        ("scaler", scaler),
        ("lstm", LSTMModel(
            sequence_length=30,  # Reducido para mejor performance
            lstm_units=[32, 16],  # Reducido para mejor performance
            dropout_rate=0.2,
            learning_rate=0.001,
            epochs=20,  # Reducido para pruebas
            batch_size=16
        )),
    ])

# =========================
# ENTRENAMIENTO
# =========================
def train_and_save():
    """Función principal para entrenar y guardar modelos"""
    print("🚀 Iniciando entrenamiento de modelos...")
    
    # 1. Cargar datos
    df = load_and_prepare_data(DATA_PATH)
    print(f"📈 Columnas disponibles: {df.columns.tolist()}")
    
    # 2. Dividir datos
    train_df, test_df = temporal_train_test_split(df, Config.TEST_SIZE)
    
    # 3. Crear pipelines
    print("\n🔨 Creando pipelines...")
    pipelines = {}
    
    # SARIMA pipelines
    sarima_pipes = create_sarima_pipelines(train_df)
    pipelines.update(sarima_pipes)
    
    # SARIMAX pipelines (opcional, comentar si es muy lento)
    # sarimax_pipes = create_sarimax_pipelines(train_df)
    # pipelines.update(sarimax_pipes)
    
    # VAR pipeline
    var_pipe = create_var_pipeline(train_df)
    pipelines["var_multivariate"] = var_pipe
    
    # LSTM pipeline (opcional, comentar si no tienes tensorflow)
    # lstm_pipe = create_lstm_pipeline(train_df)
    # pipelines["lstm_multivariate"] = lstm_pipe
    
    # 4. Entrenar y guardar modelos
    print(f"\n🎯 Entrenando {len(pipelines)} modelos...")
    
    for name, pipeline in pipelines.items():
        print(f"\n➡️ Entrenando: {name}")
        try:
            # Entrenar pipeline
            pipeline.fit(train_df)
            print(f"   ✅ Entrenado exitosamente")
            
            # Guardar modelo
            save_path = MODELS_PATH / f"{name}_model.pkl"
            joblib.dump(pipeline, save_path, compress=3)  # compress para archivos más pequeños
            print(f"   💾 Guardado en: {save_path}")
            
        except Exception as e:
            print(f"   ❌ Error entrenando {name}: {str(e)}")
    
    print(f"\n✅ Entrenamiento completado!")
    print(f"📁 Modelos guardados en: {MODELS_PATH}")
    
    # 5. Verificar que se guardaron
    model_files = list(MODELS_PATH.glob("*.pkl"))
    print(f"\n📋 Modelos guardados ({len(model_files)}):")
    for file in model_files:
        print(f"   • {file.name}")

if __name__ == "__main__":
    train_and_save()