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

UPLOADS_PATH = BASE_DIR / "uploads" 
MODELS_PATH = DIR_APP / "models"

MODELS_PATH.mkdir(exist_ok=True)

class Config:
    def __init__(self, data_filename, sarima_order, sarima_seasonal_order, var_maxlags, test_size):
        self.data_filename = data_filename
        self.SARIMA_ORDER = sarima_order
        self.SARIMA_SEASONAL_ORDER = sarima_seasonal_order
        self.VAR_MAXLAGS = var_maxlags
        self.TEST_SIZE = test_size

# =========================
# FUNCIONES AUXILIARES
# =========================
def load_and_prepare_data(data_filename, progress_tracker) -> pd.DataFrame:
    """Cargar y preparar datos para entrenamiento"""

    DATA_PATH = UPLOADS_PATH / data_filename

    progress_tracker.update_progress(1, f"📂 Cargando datos de: {DATA_PATH}")


    
    df = pd.read_csv(DATA_PATH)
    
    # Detectar columna de fecha
    date_cols = [col for col in df.columns if 'fecha' in col.lower()]
    if date_cols:
        df = pd.read_csv(DATA_PATH, parse_dates=[date_cols[0]], index_col=date_cols[0])
    else:
        df = pd.read_csv(DATA_PATH)
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            df.set_index('Fecha', inplace=True)
    
    
    progress_tracker.update_progress(1, f"✅ Datos cargados: {df.shape[0]} filas, {df.shape[1]} columnas")
    progress_tracker.update_progress(1, f'📅 Rango temporal: {df.index.min().strftime("%Y-%m-%d")} a {df.index.max().strftime("%Y-%m-%d")}')
    progress_tracker.update_progress(1, f'📋 Columnas disponibles: {", ".join(df.columns.tolist()[:5])}...')

    # Mostrar primeras y últimas filas
    progress_tracker.update_progress(1, '📊 Primeras 3 filas:')
    for idx, row in df.head(3).iterrows():
        progress_tracker.update_progress(1, f'  {idx.strftime("%Y-%m-%d")}: {row.to_dict()}')

    progress_tracker.update_progress(1, '📊 Últimas 3 filas:')
    for idx, row in df.tail(3).iterrows():
        progress_tracker.update_progress(1, f'  {idx.strftime("%Y-%m-%d")}: {row.to_dict()}')
       
        
    return df

def temporal_train_test_split(df, test_size, progress_tracker):
    """Dividir datos en train/test temporalmente"""
    split = len(df) - test_size
    train_df = df.iloc[:split]
    test_df = df.iloc[split:]
    
    progress_tracker.update_progress(2, f"📊 Split temporal: Train={len(train_df)}, Test={len(test_df)}")

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
def create_sarima_pipelines(df, config):
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
                order=config.SARIMA_ORDER,
                seasonal_order=config.SARIMA_SEASONAL_ORDER,
            ))
        ])
    
    return pipelines

def create_sarimax_pipelines(df, config):
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
                order=config.SARIMA_ORDER,
                seasonal_order=config.SARIMA_SEASONAL_ORDER,
            ))
        ])
    
    return pipelines

def create_var_pipeline(df, config):
    """Crear pipeline VAR multivariante"""
    print("🔄 Creando pipeline VAR multivariante")
    scaler = create_custom_scaler(df)
    
    return Pipeline([
        ("scaler", scaler),
        ("var", VarModel(maxlags=config.VAR_MAXLAGS)),
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
def train_and_save(progress_tracker, config):
    """Función principal para entrenar y guardar modelos"""    
    # 1. Cargar datos
    df = load_and_prepare_data(config.data_filename, progress_tracker)
    
    # 2. Dividir datos
    train_df, test_df = temporal_train_test_split(df, config.TEST_SIZE, progress_tracker)
    
    # 3. Crear pipelines
    progress_tracker.update_progress(3, "\n🔨 Creando pipelines...")
    
    pipelines = {}
    
    # SARIMA pipelines
    sarima_pipes = create_sarima_pipelines(train_df, config)
    pipelines.update(sarima_pipes)
    
    # SARIMAX pipelines (opcional, comentar si es muy lento)
    # sarimax_pipes = create_sarimax_pipelines(train_df, config)
    # pipelines.update(sarimax_pipes)
    
    # VAR pipeline
    var_pipe = create_var_pipeline(train_df, config)
    pipelines["var_multivariate"] = var_pipe
    
    # LSTM pipeline (opcional, comentar si no tienes tensorflow)
    # lstm_pipe = create_lstm_pipeline(train_df)
    # pipelines["lstm_multivariate"] = lstm_pipe
    
    # Agregación de la cantidad de elementos por cada clave del dicc
    total_models = sum(len(v) for v in pipelines.values())
    substeps_per_model = 4
    total_substeps = total_models * substeps_per_model
                       
    # 4. Entrenar y guardar modelos
    progress_tracker.update_progress(4, f"\n🎯 Entrenando {len(pipelines)} modelos...")
    
    for name, pipeline in pipelines.items():
        progress_tracker.update_progress(None, f"\n➡️ Entrenando: {name}", is_substep=True, substep_total=total_substeps)


        try:
            # Entrenar pipeline
            pipeline.fit(train_df)
            progress_tracker.update_progress(None, f"   ✅ Entrenado exitosamente", is_substep=True)            
            # Guardar modelo
            save_path = MODELS_PATH / f"{name}_model.pkl"
            joblib.dump(pipeline, save_path, compress=3)  # compress para archivos más pequeños
            progress_tracker.update_progress(None, f"   💾 Guardado en: {save_path}", is_substep=True)            
            
        except Exception as e:
            progress_tracker.update_progress(4, f"   ❌ Error entrenando {name}: {str(e)}")       


    # Verificar que se guardaron
    model_files = list(MODELS_PATH.glob("*.pkl"))
    for file in model_files:
        progress_tracker.update_progress(None, f"   • {file.name}", is_substep=True)          
    

    progress_tracker.update_progress(4, f"\n✅ Entrenamiento completado!")            
    progress_tracker.update_progress(4, f"📁 Modelos guardados en: {MODELS_PATH}")            

           