import joblib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import base64
import io
from app.ml_models import SarimaModel, SarimaxModel, VarModel, LSTMModel


MODELS_PATH = Path(__file__).resolve().parent / "models"
UPLOAD_FOLDER = Path(__file__).resolve().parent.parent / "uploads"

# Configuración de gráficos
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ====================
# FUNCIONES DE PREDICCIÓN
# ====================

def load_selected_models(selected_types, progress_tracker):
    # Lo convertimos a lista, ya que originalmente es un string 
    if isinstance(selected_types, str):
        selected_types = [selected_types]
        
    """Cargar modelos con actualización de progreso"""
    progress_tracker.update_progress(1, '🔍 Buscando modelos entrenados...')
    
    models = {}
    if not MODELS_PATH.exists():
        progress_tracker.update_progress(1, f'❌ Directorio no encontrado: {MODELS_PATH}')
        return models, progress_tracker

    model_files = []
    for type in selected_types:
        model_files.extend(MODELS_PATH.glob(f"{type}_*.pkl"))
    # model_files.extend(MODELS_PATH.iterdir())
    
    if not model_files:
        progress_tracker.update_progress(1, '❌ No se encontraron archivos .pkl')
        return models, progress_tracker


    
    progress_tracker.update_progress(1, f'📁 Encontrados {len(model_files)} archivos .pkl')
    
    for file_path in model_files:


        model_name = file_path.stem.replace('_model', '')
        progress_tracker.update_progress(1, f'  📥 Cargando modelo: {model_name}', 
                       is_substep=True, substep_total=len(model_files))
        
        try:
            model = joblib.load(file_path)

            models[model_name] = model
            progress_tracker.update_progress(1, f'    ✅ {model_name} cargado exitosamente',
                           is_substep=True, substep_total=len(model_files))
        except Exception as e:
            progress_tracker.update_progress(1, f'    ❌ Error cargando {model_name}: {str(e)}',
                           is_substep=True, substep_total=len(model_files))
    
    progress_tracker.update_progress(1, f'📊 Total modelos cargados: {len(models)}')
    return models


def load_selected_file(file_path: str, progress_tracker) -> pd.DataFrame:
    """Cargar y preparar los datos temporales"""
    
    progress_tracker.update_progress(2, '📂 Buscando archivos de datos...')

    file_path = UPLOAD_FOLDER / file_path 

    # Cargar datos (ajusta según tu fuente real)
    df = pd.read_csv(file_path, index_col='Fecha', parse_dates=True)

    try:
        progress_tracker.update_progress(2, f'📁 Cargando datos de: {file_path}')

        # Verificar que el índice es temporal y está ordenado
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        df = df.sort_index()
        
        # Completar fechas faltantes si es necesario
        full_date_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
        df = df.reindex(full_date_range)
        
        # Interpolar valores faltantes
        df = df.interpolate(method='time')

        # Mostrar primeras y últimas filas
        progress_tracker.update_progress(2, '📊 Primeras 3 filas:')
        for idx, row in df.head(3).iterrows():
            progress_tracker.update_progress(None, f'  {idx.strftime("%Y-%m-%d")}: {row.to_dict()}', 
                        is_substep=True, substep_total=3)
        
        progress_tracker.update_progress(2, '📊 Últimas 3 filas:')
        for idx, row in df.tail(3).iterrows():
            progress_tracker.update_progress(None, f'  {idx.strftime("%Y-%m-%d")}: {row.to_dict()}', 
                        is_substep=True, substep_total=3)
            
        
        # Mostrar información detallada
        progress_tracker.update_progress(2, f'✓ Datos cargados: {df.shape[0]} filas, {df.shape[1]} columnas')
        progress_tracker.update_progress(2, f'📅 Rango temporal: {df.index.min().strftime("%Y-%m-%d")} a {df.index.max().strftime("%Y-%m-%d")}')
        progress_tracker.update_progress(2, f'📋 Columnas disponibles: {", ".join(df.columns.tolist()[:5])}...')

    except Exception as e:
        progress_tracker.update_progress(2, f'❌ Error cargando datos: {str(e)}')
        raise

    return df

def make_future_predictions(progress_tracker, loaded_models: dict, last_available_data: pd.DataFrame, horizon: int = 45):
    """Hacer predicciones futuras con modelos cargados"""
    
    predictions = {}
    
    progress_tracker.update_progress(3, f'🎯 Generando predicciones para {horizon} días')


    for name, model in loaded_models.items():
        try:
            pred = model.predict(last_available_data, n_periods=horizon)
            predictions[name] = pred
            progress_tracker.update_progress(3, f'✓ Predicción futura generada para {name}')
        except Exception as e:
            progress_tracker.update_progress(3, f'✗ Error en predicción para {name}: {str(e)}')
    
    return predictions


def unify_predictions(predictions_dict, progress_tracker):
    """Unificar predicciones con actualización de progreso"""
    progress_tracker.update_progress(4, 'Unificando predicciones...')


    unified_predictions_dict = {
        'sarima': None,
        'sarimax': None,
        'var_multivariate': None,
        'lstm_multivariate': None
    }
            
    for name, prediction_df in predictions_dict.items():  
        if name.startswith('sarima_'):
            unified_predictions_dict['sarima'] = pd.concat([unified_predictions_dict['sarima'], prediction_df], axis=1, join="inner")
        
        elif name.startswith('sarimax_'):
            unified_predictions_dict['sarimax'] = pd.concat([unified_predictions_dict['sarimax'], prediction_df], axis=1, join="inner")

        else:
            unified_predictions_dict[f'{name}'] = prediction_df

    # Eliminar aquellos modelos que no han sido predichos para evitar None posteriores
    unified_predictions_dict = {k: v for k, v in unified_predictions_dict.items() if v is not None}

    for name in unified_predictions_dict.keys():  
        unified_predictions_dict[name].columns = ['Presión atmosférica', 'Humedad relativa mínima', 'Velocidad del viento', 'Temperatura',  'Radiación solar', 'Precipitaciones', 'Humedad relativa']


    print(f'Unified predictions dict{unified_predictions_dict}')

    progress_tracker.update_progress(4, '✓ Predicciones unificadas exitosamente')
    
               
    return unified_predictions_dict

def calculate_et0_fao_penman_monteith(df):
    """
    Calcula la Evapotranspiración de Referencia (ET0) usando la ecuación FAO Penman-Monteith
    """
    
    # Obtener datos del dataframe
    T = df['Temperatura']  # Temperatura media del aire [°C]
    RH = df['Humedad relativa']  # Humedad relativa [%]
    u2 = df['Velocidad del viento']  # Velocidad del viento a 2m [m/s]
    P = df['Presión atmosférica'] * 0.1  # Convertir hPa a kPa
    Rs = df['Radiación solar'] / 1e6  # Convertir J/m²/día a MJ/m²/día
    
    # 1. PRESIÓN DE VAPOR DE SATURACIÓN (es)
    # Fórmula: es = 0.6108 * exp(17.27 * T / (T + 237.3))
    es = 0.6108 * np.exp(17.27 * T / (T + 237.3))
    
    # 2. PRESIÓN DE VAPOR ACTUAL (ea)
    # Fórmula: ea = (RH/100) * es
    ea = es * RH / 100
    
    # 3. PENDIENTE DE LA CURVA DE PRESIÓN DE VAPOR (Δ)
    # Fórmula: Δ = 4098 * es / (T + 237.3)²
    delta = 4098 * es / (T + 237.3)**2
    
    # 4. CONSTANTE PSICROMÉTRICA (γ)
    # Fórmula: γ = 0.665 × 10⁻³ * P
    gamma = 0.665 * 1e-3 * P
    
    # 5. RADIACIÓN NETA (Rn) - Simplificada
    # Fórmula: Rn = 0.77 * Rs (asumiendo albedo 0.23)
    Rn = (1 - 0.23) * Rs
    
    # 6. FLUJO DE CALOR DEL SUELO (G) - Cero para periodos diarios
    G = 0
    
    # 7. ECUACIÓN FAO PENMAN-MONTEITH COMPLETA
    # Fórmula: 
    # ET0 = [0.408 * Δ * (Rn - G) + γ * (900/(T + 273)) * u2 * (es - ea)] / 
    #        [Δ + γ * (1 + 0.34 * u2)]
    
    numerador = (0.408 * delta * (Rn - G) + 
                gamma * (900 / (T + 273)) * u2 * (es - ea))
    
    denominador = delta + gamma * (1 + 0.34 * u2)
    
    et0 = numerador / denominador
    
    return et0

def calcular_Kc(dia , progress_tracker):

    kc_ini = 0.4
    kc_mid = 0.9
    kc_end = 0.65

        # Duración de las etapas (días)
    L_ini = 15    # Etapa inicial
    L_dev = 50    # Etapa de desarrollo  
    L_mid = 98    # Etapa de mediados
    L_late = 31   # Etapa final

    # Puntos de transición entre etapas
    dia_fin_ini = L_ini
    dia_fin_dev = L_ini + L_dev
    dia_fin_mid = L_ini + L_dev + L_mid
    dia_fin_late = L_ini + L_dev + L_mid + L_late

    if dia <= dia_fin_ini:
        # Etapa inicial: Kc constante
        return kc_ini
    elif dia <= dia_fin_dev:
        # Etapa desarrollo: línea diagonal ascendente
        progreso = (dia - dia_fin_ini) / L_dev
        return kc_ini + progreso * (kc_mid - kc_ini)
    elif dia <= dia_fin_mid:
        # Etapa mediados: Kc constante
        return kc_mid
    elif dia <= dia_fin_late:
        # Etapa final: línea diagonal descendente
        progreso = (dia - dia_fin_mid) / L_late
        return kc_mid + progreso * (kc_end - kc_mid)
    else:
        return kc_end
    

# Calcular ETc para un día específico 
def calcular_ETc(dia, ETo, progress_tracker):
    """Calcula ETc para un día específico dado ETo"""
    kc = calcular_Kc(dia, progress_tracker)
    return kc * ETo




def calculate_irrigation(predictions_df, progress_tracker):
    """Calcular riego con actualización de progreso"""
    progress_tracker.update_progress(5, '💧 Calculando necesidades de riego...')
    
    if predictions_df.empty:
        progress_tracker.update_progress(5, '❌ No hay datos para calcular riego')
        raise FileNotFoundError("No hay datos para calcular riego")

    # Aplicar al dataframe
    predictions_df['ET0'] = calculate_et0_fao_penman_monteith(predictions_df)

    # Necesario para que el indice se DateTmeIndex y podamos usar .dayofyear
    predictions_df.index = pd.to_datetime(predictions_df.index)

    predictions_df["dia"] = predictions_df.index.dayofyear

    predictions_df["ETc"] = predictions_df.apply(lambda fila: calcular_ETc(fila["dia"], fila["ET0"], progress_tracker), axis=1)

    # --- Configuración de parámetros ---
    EFICIENCIA_RIEGO = 0.95  # Ajustar según sistema (0.95 para goteo)
    COEF_PRECIPITACION = 0.75 # Porcentaje de lluvia aprovechable (75%)

    # Definimos la Precipitación Efectiva (Pe)
    # Se suele considerar efectiva si la lluvia supera un umbral mínimo (3 mm), como indica la FAO-56
    def calcular_pe(precipitacion):
        if precipitacion > 3:
            return precipitacion * COEF_PRECIPITACION
        return 0

    predictions_df["Pe"] = predictions_df["Precipitaciones"].apply(calcular_pe)

    # Calculamos Necesidades Netas (NN = ETc - Pe)
    predictions_df["NN"] = (predictions_df["ETc"] - predictions_df["Pe"]).clip(lower=0)

    # Calculamos Necesidades Brutas (NB = NN / Eficiencia)
    predictions_df["NB"] = predictions_df["NN"] / EFICIENCIA_RIEGO

    # Visualizar resultados
    print(predictions_df[["Precipitaciones", "ETc", "Pe", "NN", "NB"]].head())

    # Calculamos ETc_RDC y lo aplicamos al dataframe en su propia columna
    predictions_df["ETc_RDC"] = predictions_df.apply(lambda fila: calcular_ETc(fila["dia"], fila["ET0"], progress_tracker) * 0.2, axis=1)

    # Calculamos Necesidades Netas (NN = ETc - Pe)
    predictions_df["NN_RDC"] = (predictions_df["ETc_RDC"] - predictions_df["Pe"]).clip(lower=0)

    # Calculamos Necesidades Brutas (NB = NN / Eficiencia)
    predictions_df["NB_RDC"] = predictions_df["NN_RDC"] / EFICIENCIA_RIEGO

    # Visualizar resultados
    print(predictions_df[["Precipitaciones", "ETc_RDC", "Pe", "NN_RDC", "NB_RDC"]].head())
    
    progress_tracker.update_progress(5, f'💦 Cálculo completado: {len(predictions_df)} días')
    progress_tracker.update_progress(5, f'📈 Riego total: {predictions_df["NB"].sum():.2f} mm')
    progress_tracker.update_progress(5, f'📈 Riego total con RDC: {predictions_df["NB_RDC"].sum():.2f} mm')
    progress_tracker.update_progress(5, f'📊 Riego promedio con RDC: {predictions_df["NB_RDC"].mean():.2f} mm/día')
    
    return predictions_df


def create_prediction_plots(predictions_df, progress_tracker):
    """Crear gráficos con actualización de progreso"""
    progress_tracker.update_progress(6, '🎨 Generando visualizaciones...')
    
    plots = {}
    
    # Gráfico 1: Riego
    progress_tracker.update_progress(6, '📊 Creando gráfico de riego...', is_substep=True, substep_total=3)
    try:
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(predictions_df.index, predictions_df['NB'], 
                color='blue', linewidth=2, marker='o', markersize=4)
        ax1.fill_between(predictions_df.index, 0, predictions_df['NB'], 
                        alpha=0.3, color='lightblue')
        ax1.set_title('Necesidad de Riego Predicha', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Fecha')
        ax1.set_ylabel('Riego (mm/día)')
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        
        img1 = io.BytesIO()
        plt.savefig(img1, format='png', dpi=100, bbox_inches='tight')
        img1.seek(0)
        plots['riego'] = base64.b64encode(img1.getvalue()).decode()
        plt.close(fig1)
        progress_tracker.update_progress(6, '  ✅ Gráfico de riego generado')
    except Exception as e:
        progress_tracker.update_progress(6, f'  ❌ Error en gráfico de riego: {e}')
    
    # Gráfico 2: Variables principales
    progress_tracker.update_progress(6, '📈 Creando gráfico de variables...', is_substep=True, substep_total=3)
    try:
        main_vars = []
        for var in ['Temperatura', 'Humedad relativa', 'Precipitaciones', 'ETc']:
            matching = [col for col in predictions_df.columns if var in col]
            if matching:
                main_vars.append(matching[0])
        
        if main_vars and len(main_vars) <= 4:
            fig2, axes = plt.subplots(2, 2, figsize=(15, 10))
            axes = axes.flatten()
            
            for i, var in enumerate(main_vars[:4]):
                ax = axes[i]
                ax.plot(predictions_df.index, predictions_df[var], 
                       linewidth=2, alpha=0.7)
                if var == 'ETc':
                    ax.set_title(f'Cálculo: {var}')
                ax.set_title(f'Predicción: {var}')
                ax.set_xlabel('Fecha')
                ax.set_ylabel(var)
                ax.grid(True, alpha=0.3)
                ax.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            img2 = io.BytesIO()
            plt.savefig(img2, format='png', dpi=100, bbox_inches='tight')
            img2.seek(0)
            plots['variables'] = base64.b64encode(img2.getvalue()).decode()
            plt.close(fig2)
            progress_tracker.update_progress(6, f'  ✅ Gráfico de {len(main_vars)} variables generado')
    except Exception as e:
        progress_tracker.update_progress(6, f'  ❌ Error en gráfico de variables: {e}')
    
    progress_tracker.update_progress(6, '✅ Visualizaciones completadas', is_substep=True, substep_total=3)
    return plots
