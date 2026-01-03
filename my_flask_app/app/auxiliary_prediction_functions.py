import joblib
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import base64
import io
import os


MODELS_PATH = Path(__file__).resolve().parent / "models"
UPLOAD_FOLDER = "uploads"


# Configuración de gráficos
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ====================
# FUNCIONES DE PREDICCIÓN
# ====================



def load_all_models(progress_tracker):
    """Cargar modelos con actualización de progreso"""
    progress_tracker.update_progress(1, '🔍 Buscando modelos entrenados...')
    
    models = {}
    if not MODELS_PATH.exists():
        progress_tracker.update_progress(1, f'❌ Directorio no encontrado: {MODELS_PATH}')
        return models, progress_tracker

    
    model_files = list(MODELS_PATH.glob("*.pkl"))
    
    if not model_files:
        progress_tracker.update_progress(1, '❌ No se encontraron archivos .pkl')
        return models, progress_tracker


    
    progress_tracker.update_progress(1, f'📁 Encontrados {len(model_files)} archivos .pkl')
    
    for i, file_path in enumerate(model_files):
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

def load_latest_data(progress_tracker):
    """Cargar datos con actualización de progreso"""
    progress_tracker.update_progress(2, '📂 Buscando archivos de datos...')
    
    data_files = list(Path(UPLOAD_FOLDER).glob("*.csv"))
    
    if not data_files:
        raise FileNotFoundError("No hay archivos de datos en la carpeta uploads")
    
    latest_file = max(data_files, key=os.path.getctime)
    progress_tracker.update_progress(2, f'📁 Cargando datos de: {latest_file.name}')
    
    try:
        df = pd.read_csv(latest_file)
        
        # Detectar columna de fecha
        date_cols = [col for col in df.columns if 'fecha' in col.lower()]
        if date_cols:
            df['Fecha'] = pd.to_datetime(df[date_cols[0]])
            df.set_index('Fecha', inplace=True)
        elif 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'])
            df.set_index('Fecha', inplace=True)
        else:
            last_date = datetime.now() - timedelta(days=len(df))
            df['Fecha'] = pd.date_range(start=last_date, periods=len(df), freq='D')
            df.set_index('Fecha', inplace=True)
        
        # Mostrar información detallada
        progress_tracker.update_progress(2, f'✅ Datos cargados: {df.shape[0]} filas, {df.shape[1]} columnas')
        progress_tracker.update_progress(2, f'📅 Rango temporal: {df.index.min().strftime("%Y-%m-%d")} a {df.index.max().strftime("%Y-%m-%d")}')
        progress_tracker.update_progress(2, f'📋 Columnas disponibles: {", ".join(df.columns.tolist()[:5])}...')
        
        # Mostrar primeras y últimas filas
        progress_tracker.update_progress(2, '📊 Primeras 3 filas:')
        for idx, row in df.head(3).iterrows():
            progress_tracker.update_progress(2, f'  {idx.strftime("%Y-%m-%d")}: {row.to_dict()}', 
                           is_substep=True, substep_total=3)
        
        progress_tracker.update_progress(2, '📊 Últimas 3 filas:')
        for idx, row in df.tail(3).iterrows():
            progress_tracker.update_progress(2, f'  {idx.strftime("%Y-%m-%d")}: {row.to_dict()}', 
                           is_substep=True, substep_total=3)
        
        return df

        
    except Exception as e:
        progress_tracker.update_progress(2, f'❌ Error cargando datos: {str(e)}')
        raise

def make_predictions(models_dict, last_data, horizon_days, progress_tracker):
    """Realizar predicciones con actualización de progreso"""
    predictions = {}
    
    if not models_dict:
        progress_tracker.update_progress(3, '❌ No hay modelos cargados para hacer predicciones')
        return predictions

    
    progress_tracker.update_progress(3, f'🎯 Generando predicciones para {horizon_days} días')
    
    # Separar modelos por tipo
    sarima_models = {k: v for k, v in models_dict.items() if 'sarima_' in k}
    sarimax_models = {k: v for k, v in models_dict.items() if 'sarimax_' in k}
    var_model = models_dict.get('var_multivariate')
    lstm_model = models_dict.get('lstm_multivariate')
    
    progress_tracker.update_progress(3, f'  1️⃣  📊 SARIMA: {len(sarima_models)}, SARIMAX: {len(sarimax_models)}')
    progress_tracker.update_progress(3, f'  2️⃣  📈 VAR: {"✅" if var_model else "❌"}, LSTM: {"✅" if lstm_model else "❌"}')
    
    # Predicciones SARIMA
    sarima_count = 0
    for name, pipeline in sarima_models.items():
        try:
            var_name = name.replace('sarima_', '')
            if var_name in last_data.columns:
                sarima_count += 1
                progress_tracker.update_progress(3, f'  {sarima_count+2:2d} 🔮 Prediciendo SARIMA para: {var_name}')
                
                pred = pipeline.predict(last_data, n_periods=horizon_days)
                
                if hasattr(pred, 'values'):
                    predictions[var_name] = pred.values
                else:
                    predictions[var_name] = np.array(pred)
                
                progress_tracker.update_progress(3, f'      ✅ SARIMA {var_name}: {len(predictions[var_name])} valores',
                               is_substep=True, substep_total=len(sarima_models))
                
        except Exception as e:
            progress_tracker.update_progress(3, f'      ❌ Error en SARIMA {name}: {str(e)}',
                           is_substep=True, substep_total=len(sarima_models))
    
    # Predicción VAR
    if var_model:
        progress_tracker.update_progress(3, f'  {len(sarima_models)+3:2d} 🔮 Prediciendo VAR multivariante')
        try:
            var_pred = var_model.predict(last_data, n_periods=horizon_days)
            
            for col in var_pred.columns:
                predictions[f'VAR_{col}'] = var_pred[col].values
            
            progress_tracker.update_progress(3, f'      ✅ VAR: {var_pred.shape[1]} variables predichas')
            
        except Exception as e:
            progress_tracker.update_progress(3, f'      ❌ Error en VAR: {str(e)}')
    
    # Predicción LSTM
    if lstm_model:
        progress_tracker.update_progress(3, f'  {len(sarima_models)+4:2d} 🔮 Prediciendo LSTM multivariante')
        try:
            lstm_pred = lstm_model.predict(last_data, n_periods=horizon_days)
            
            for col in lstm_pred.columns:
                predictions[f'LSTM_{col}'] = lstm_pred[col].values
            
            progress_tracker.update_progress(3, f'      ✅ LSTM: {lstm_pred.shape[1]} variables predichas')
            
        except Exception as e:
            progress_tracker.update_progress(3, f'      ❌ Error en LSTM: {str(e)}')
    
    progress_tracker.update_progress(3, f'🎉 Total predicciones generadas: {len(predictions)}')
    return predictions


def unify_predictions(predictions_dict, horizon_days, progress_tracker):
    """Unificar predicciones con actualización de progreso"""
    progress_tracker.update_progress(4, '🔄 Unificando predicciones...')
    
    if not predictions_dict:
        progress_tracker.update_progress(4, '❌ No hay predicciones para unificar')
        return pd.DataFrame()

    
    # Mostrar qué predicciones se van a unificar
    sarima_predictions = [k for k in predictions_dict.keys() if not k.startswith(('VAR_', 'LSTM_', 'SARIMA'))]
    
    progress_tracker.update_progress(4, f'📋 SARIMA predictions: {len(sarima_predictions)} variables')
    
    # Crear DataFrame unificado
    future_dates = pd.date_range(
        start=datetime.now() + timedelta(days=1),
        periods=horizon_days,
        freq='D'
    )
    
    unified_df = pd.DataFrame(index=future_dates)
    unified_df.index.name = 'Fecha'
    
    for var_name, pred_values in predictions_dict.items():
        if len(pred_values) >= horizon_days:
            unified_df[var_name] = pred_values[:horizon_days]
        else:
            unified_df[var_name] = np.pad(
                pred_values,
                (0, horizon_days - len(pred_values)),
                'edge'
            )
    
    progress_tracker.update_progress(4, f'📊 DataFrame unificado: {unified_df.shape[0]} filas × {unified_df.shape[1]} columnas')
    progress_tracker.update_progress(4, '✅ Predicciones unificadas exitosamente')
    
    return unified_df


def calculate_irrigation(predictions_df, progress_tracker):
    """Calcular riego con actualización de progreso"""
    progress_tracker.update_progress(5, '💧 Calculando necesidades de riego...')
    
    if predictions_df.empty:
        progress_tracker.update_progress(5, '❌ No hay datos para calcular riego')
        return pd.DataFrame()

    
    # Mostrar fórmula de cálculo
    progress_tracker.update_progress(5, '📐 Fórmula aplicada:')
    progress_tracker.update_progress(5, '  ET₀ = 0.0023 × (Tmean + 17.8) × Radiación × 0.0864')
    progress_tracker.update_progress(5, '  Riego = max(0, ET₀ × Kc × factor_humedad + ajuste_precipitación)')
    progress_tracker.update_progress(5, '  Donde: Kc = 0.8, factor_humedad = max(0.7, 1 - (humedad - 60)/100)')
    
    irrigation_data = []
    
    # Calcular para cada día
    total_days = len(predictions_df)
    for idx, row in predictions_df.iterrows():
        # Buscar variables
        temp_key = next((col for col in predictions_df.columns 
                        if 'temperatura' in col.lower()), None)
        precip_key = next((col for col in predictions_df.columns 
                          if 'precipitacion' in col.lower()), None)
        humidity_key = next((col for col in predictions_df.columns 
                           if 'humedad' in col.lower()), None)
        radiation_key = next((col for col in predictions_df.columns 
                            if 'radiacion' in col.lower()), None)
        
        # Valores
        temp = row[temp_key] if temp_key else 20.0
        precip = row[precip_key] if precip_key else 0.0
        humidity = row[humidity_key] if humidity_key else 60.0
        radiation = row[radiation_key] if radiation_key else 5.0
        
        # Cálculo
        et0 = 0.0023 * (temp + 17.8) * radiation * 0.0864
        kc = 0.8
        humidity_factor = max(0.7, 1 - (humidity - 60) / 100)
        precip_adjustment = -min(precip, 5)
        irrigation_needs = max(0, et0 * kc * humidity_factor + precip_adjustment)
        
        irrigation_data.append({
            'Fecha': idx,
            'Riego_mm': round(irrigation_needs, 2),
            'Temperatura_estimada': round(temp, 1),
            'Precipitacion_estimada': round(precip, 1),
            'Humedad_estimada': round(humidity, 1),
            'Radiacion_estimada': round(radiation, 1),
            'ET0_estimada': round(et0, 2)
        })
        
        # Actualizar progreso cada 10 días
        if len(irrigation_data) % max(1, total_days//10) == 0:
            progress_pct = (len(irrigation_data) / total_days) * 100
            progress_tracker.update_progress(5, f'  📅 Día {len(irrigation_data)}/{total_days} ({progress_pct:.0f}%)',
                           is_substep=True, substep_total=total_days)
    
    irrigation_df = pd.DataFrame(irrigation_data)
    progress_tracker.update_progress(5, f'💦 Cálculo completado: {len(irrigation_df)} días')
    progress_tracker.update_progress(5, f'📈 Riego total: {irrigation_df["Riego_mm"].sum():.2f} mm')
    progress_tracker.update_progress(5, f'📊 Riego promedio: {irrigation_df["Riego_mm"].mean():.2f} mm/día')
    
    return irrigation_df


def create_prediction_plots(predictions_df, irrigation_df, last_data, progress_tracker):
    """Crear gráficos con actualización de progreso"""
    progress_tracker.update_progress(6, '🎨 Generando visualizaciones...')
    
    plots = {}
    
    # Gráfico 1: Riego
    progress_tracker.update_progress(6, '📊 Creando gráfico de riego...', is_substep=True, substep_total=3)
    try:
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(irrigation_df['Fecha'], irrigation_df['Riego_mm'], 
                color='blue', linewidth=2, marker='o', markersize=4)
        ax1.fill_between(irrigation_df['Fecha'], 0, irrigation_df['Riego_mm'], 
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
        for var in ['temperatura', 'humedad', 'precipitacion', 'radiacion']:
            matching = [col for col in predictions_df.columns if var in col.lower()]
            if matching:
                main_vars.append(matching[0])
        
        if main_vars and len(main_vars) <= 4:
            fig2, axes = plt.subplots(2, 2, figsize=(15, 10))
            axes = axes.flatten()
            
            for i, var in enumerate(main_vars[:4]):
                ax = axes[i]
                ax.plot(predictions_df.index, predictions_df[var], 
                       linewidth=2, alpha=0.7)
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
