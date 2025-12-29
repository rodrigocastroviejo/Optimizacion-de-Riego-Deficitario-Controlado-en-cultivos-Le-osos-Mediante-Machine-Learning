# routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, send_file, session
from werkzeug.utils import secure_filename
from app import db
from app.models import Dataset, User
import os
from flask_login import login_user, logout_user, login_required, current_user

import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime, timedelta
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Para evitar problemas con hilos en Flask
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Importar el registro de clases personalizadas PRIMERO
from app.model_registry import register_custom_classes
register_custom_classes()

from app.progress_tracker import init_prediction_progress, update_progress, complete_progress

main = Blueprint("main", __name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}
MODELS_PATH = Path(__file__).resolve().parent / "models"

# Configuración de gráficos
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ====================
# RUTAS BÁSICAS (mantén las existentes)
# ====================

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not username or not email or not password:
            flash("Completa todos los campos.", "danger")
            return redirect(url_for("main.register"))
        if User.query.filter((User.username==username)|(User.email==email)).first():
            flash("El usuario o email ya existe.", "danger")
            return redirect(url_for("main.register"))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Registro correcto. Ahora inicia sesión.", "success")
        return redirect(url_for("main.login"))
    return render_template("register.html")

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Sesión iniciada.", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.upload_file"))
        flash("Usuario o contraseña incorrectos.", "danger")
        return redirect(url_for("main.login"))
    return render_template("login.html")

@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("main.index"))

@main.route("/upload", methods=["GET", "POST"])
@login_required
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No se ha seleccionado archivo", "danger")
            return redirect(request.url)

        file = request.files["file"]

        if file.filename == "":
            flash("El nombre de archivo está vacío", "danger")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            file.save(upload_path)

            dataset = Dataset(filename=filename, filepath=upload_path, user_id=current_user.id)
            db.session.add(dataset)
            db.session.commit()

            flash("Archivo subido y registrado con éxito", "success")
            return redirect(url_for("main.upload_file"))
        else:
            flash("Formato no permitido. Solo CSV", "danger")
            return redirect(request.url)

    datasets = Dataset.query.filter_by(user_id=current_user.id).order_by(Dataset.uploaded_at.desc()).all()
    return render_template("upload.html", datasets=datasets)

# ====================
# FUNCIONES DE PREDICCIÓN
# ====================

def load_all_models():
    """Cargar modelos con actualización de progreso"""
    update_progress(1, '🔍 Buscando modelos entrenados...')
    
    models = {}
    if not MODELS_PATH.exists():
        update_progress(1, f'❌ Directorio no encontrado: {MODELS_PATH}')
        return models
    
    model_files = list(MODELS_PATH.glob("*.pkl"))
    
    if not model_files:
        update_progress(1, '❌ No se encontraron archivos .pkl')
        return models
    
    update_progress(1, f'📁 Encontrados {len(model_files)} archivos .pkl')
    
    for i, file_path in enumerate(model_files):
        model_name = file_path.stem.replace('_model', '')
        update_progress(1, f'  📥 Cargando modelo: {model_name}', 
                       is_substep=True, substep_total=len(model_files))
        
        try:
            model = joblib.load(file_path)
            models[model_name] = model
            update_progress(1, f'    ✅ {model_name} cargado exitosamente',
                           is_substep=True, substep_total=len(model_files))
        except Exception as e:
            update_progress(1, f'    ❌ Error cargando {model_name}: {str(e)}',
                           is_substep=True, substep_total=len(model_files))
    
    update_progress(1, f'📊 Total modelos cargados: {len(models)}')
    return models

def load_latest_data():
    """Cargar datos con actualización de progreso"""
    update_progress(2, '📂 Buscando archivos de datos...')
    
    data_files = list(Path(UPLOAD_FOLDER).glob("*.csv"))
    
    if not data_files:
        raise FileNotFoundError("No hay archivos de datos en la carpeta uploads")
    
    latest_file = max(data_files, key=os.path.getctime)
    update_progress(2, f'📁 Cargando datos de: {latest_file.name}')
    
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
        update_progress(2, f'✅ Datos cargados: {df.shape[0]} filas, {df.shape[1]} columnas')
        update_progress(2, f'📅 Rango temporal: {df.index.min().strftime("%Y-%m-%d")} a {df.index.max().strftime("%Y-%m-%d")}')
        update_progress(2, f'📋 Columnas disponibles: {", ".join(df.columns.tolist()[:5])}...')
        
        # Mostrar primeras y últimas filas
        update_progress(2, '📊 Primeras 3 filas:')
        for idx, row in df.head(3).iterrows():
            update_progress(2, f'  {idx.strftime("%Y-%m-%d")}: {row.to_dict()}', 
                           is_substep=True, substep_total=3)
        
        update_progress(2, '📊 Últimas 3 filas:')
        for idx, row in df.tail(3).iterrows():
            update_progress(2, f'  {idx.strftime("%Y-%m-%d")}: {row.to_dict()}', 
                           is_substep=True, substep_total=3)
        
        return df
        
    except Exception as e:
        update_progress(2, f'❌ Error cargando datos: {str(e)}')
        raise

def make_predictions(models_dict, last_data, horizon_days):
    """Realizar predicciones con actualización de progreso"""
    predictions = {}
    
    if not models_dict:
        update_progress(3, '❌ No hay modelos cargados para hacer predicciones')
        return predictions
    
    update_progress(3, f'🎯 Generando predicciones para {horizon_days} días')
    
    # Separar modelos por tipo
    sarima_models = {k: v for k, v in models_dict.items() if 'sarima_' in k}
    sarimax_models = {k: v for k, v in models_dict.items() if 'sarimax_' in k}
    var_model = models_dict.get('var_multivariate')
    lstm_model = models_dict.get('lstm_multivariate')
    
    update_progress(3, f'  1️⃣  📊 SARIMA: {len(sarima_models)}, SARIMAX: {len(sarimax_models)}')
    update_progress(3, f'  2️⃣  📈 VAR: {"✅" if var_model else "❌"}, LSTM: {"✅" if lstm_model else "❌"}')
    
    # Predicciones SARIMA
    sarima_count = 0
    for name, pipeline in sarima_models.items():
        try:
            var_name = name.replace('sarima_', '')
            if var_name in last_data.columns:
                sarima_count += 1
                update_progress(3, f'  {sarima_count+2:2d} 🔮 Prediciendo SARIMA para: {var_name}')
                
                pred = pipeline.predict(last_data, n_periods=horizon_days)
                
                if hasattr(pred, 'values'):
                    predictions[var_name] = pred.values
                else:
                    predictions[var_name] = np.array(pred)
                
                update_progress(3, f'      ✅ SARIMA {var_name}: {len(predictions[var_name])} valores',
                               is_substep=True, substep_total=len(sarima_models))
                
        except Exception as e:
            update_progress(3, f'      ❌ Error en SARIMA {name}: {str(e)}',
                           is_substep=True, substep_total=len(sarima_models))
    
    # Predicción VAR
    if var_model:
        update_progress(3, f'  {len(sarima_models)+3:2d} 🔮 Prediciendo VAR multivariante')
        try:
            var_pred = var_model.predict(last_data, n_periods=horizon_days)
            
            for col in var_pred.columns:
                predictions[f'VAR_{col}'] = var_pred[col].values
            
            update_progress(3, f'      ✅ VAR: {var_pred.shape[1]} variables predichas')
            
        except Exception as e:
            update_progress(3, f'      ❌ Error en VAR: {str(e)}')
    
    # Predicción LSTM
    if lstm_model:
        update_progress(3, f'  {len(sarima_models)+4:2d} 🔮 Prediciendo LSTM multivariante')
        try:
            lstm_pred = lstm_model.predict(last_data, n_periods=horizon_days)
            
            for col in lstm_pred.columns:
                predictions[f'LSTM_{col}'] = lstm_pred[col].values
            
            update_progress(3, f'      ✅ LSTM: {lstm_pred.shape[1]} variables predichas')
            
        except Exception as e:
            update_progress(3, f'      ❌ Error en LSTM: {str(e)}')
    
    update_progress(3, f'🎉 Total predicciones generadas: {len(predictions)}')
    return predictions

def unify_predictions(predictions_dict, horizon_days):
    """Unificar predicciones con actualización de progreso"""
    update_progress(4, '🔄 Unificando predicciones...')
    
    if not predictions_dict:
        update_progress(4, '❌ No hay predicciones para unificar')
        return pd.DataFrame()
    
    # Mostrar qué predicciones se van a unificar
    sarima_predictions = [k for k in predictions_dict.keys() if not k.startswith(('VAR_', 'LSTM_', 'SARIMA'))]
    
    update_progress(4, f'📋 SARIMA predictions: {len(sarima_predictions)} variables')
    
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
    
    update_progress(4, f'📊 DataFrame unificado: {unified_df.shape[0]} filas × {unified_df.shape[1]} columnas')
    update_progress(4, '✅ Predicciones unificadas exitosamente')
    
    return unified_df

def calculate_irrigation(predictions_df):
    """Calcular riego con actualización de progreso"""
    update_progress(5, '💧 Calculando necesidades de riego...')
    
    if predictions_df.empty:
        update_progress(5, '❌ No hay datos para calcular riego')
        return pd.DataFrame()
    
    # Mostrar fórmula de cálculo
    update_progress(5, '📐 Fórmula aplicada:')
    update_progress(5, '  ET₀ = 0.0023 × (Tmean + 17.8) × Radiación × 0.0864')
    update_progress(5, '  Riego = max(0, ET₀ × Kc × factor_humedad + ajuste_precipitación)')
    update_progress(5, '  Donde: Kc = 0.8, factor_humedad = max(0.7, 1 - (humedad - 60)/100)')
    
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
            update_progress(5, f'  📅 Día {len(irrigation_data)}/{total_days} ({progress_pct:.0f}%)',
                           is_substep=True, substep_total=total_days)
    
    irrigation_df = pd.DataFrame(irrigation_data)
    update_progress(5, f'💦 Cálculo completado: {len(irrigation_df)} días')
    update_progress(5, f'📈 Riego total: {irrigation_df["Riego_mm"].sum():.2f} mm')
    update_progress(5, f'📊 Riego promedio: {irrigation_df["Riego_mm"].mean():.2f} mm/día')
    
    return irrigation_df

def create_prediction_plots(predictions_df, irrigation_df, last_data):
    """Crear gráficos con actualización de progreso"""
    update_progress(6, '🎨 Generando visualizaciones...')
    
    plots = {}
    
    # Gráfico 1: Riego
    update_progress(6, '📊 Creando gráfico de riego...', is_substep=True, substep_total=3)
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
        update_progress(6, '  ✅ Gráfico de riego generado')
    except Exception as e:
        update_progress(6, f'  ❌ Error en gráfico de riego: {e}')
    
    # Gráfico 2: Variables principales
    update_progress(6, '📈 Creando gráfico de variables...', is_substep=True, substep_total=3)
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
            update_progress(6, f'  ✅ Gráfico de {len(main_vars)} variables generado')
    except Exception as e:
        update_progress(6, f'  ❌ Error en gráfico de variables: {e}')
    
    update_progress(6, '✅ Visualizaciones completadas', is_substep=True, substep_total=3)
    return plots


# ====================
# RUTAS DE PREDICCIÓN
# ====================

@main.route("/prediccion", methods=["GET", "POST"])
@login_required
def prediccion():
    """Ruta para realizar y mostrar predicciones"""
    
    if request.method == "POST":
        try:
            # Obtener parámetros del formulario
            horizon_days = int(request.form.get("horizon_days", 30))
            horizon_days = min(horizon_days, 365)  # Límite máximo
            
            print(f"\n🌐 Iniciando predicción para {horizon_days} días")
            
            # Cargar modelos
            models = load_all_models()
            if not models:
                flash("No se encontraron modelos entrenados.", "warning")
                return redirect(url_for("main.prediccion"))
            
            # Cargar datos
            last_data = load_latest_data()
            
            # Realizar predicciones
            predictions = make_predictions(models, last_data, horizon_days)
            
            if not predictions:
                flash("No se pudieron generar predicciones con los modelos disponibles.", "warning")
                return redirect(url_for("main.prediccion"))
            
            # Unificar predicciones
            unified_predictions = c(predictions, horizon_days)
            
            # Calcular riego
            irrigation_df = calculate_irrigation(unified_predictions)
            
            # Crear gráficos
            plots = create_prediction_plots(unified_predictions, irrigation_df, last_data)
            
            # Preparar datos para la vista
            prediction_summary = {
                'total_dias': horizon_days,
                'fecha_inicio': datetime.now().strftime('%Y-%m-%d'),
                'fecha_fin': (datetime.now() + timedelta(days=horizon_days)).strftime('%Y-%m-%d'),
                'num_variables': len(unified_predictions.columns),
                'riego_promedio': round(irrigation_df['Riego_mm'].mean(), 2),
                'riego_total': round(irrigation_df['Riego_mm'].sum(), 2),
                'riego_maximo': round(irrigation_df['Riego_mm'].max(), 2),
                'riego_minimo': round(irrigation_df['Riego_mm'].min(), 2)
            }
            
            # Preparar datos para tabla (primeros 15 días)
            table_data = irrigation_df.head(15).to_dict('records')
            
            # Guardar datos en sesión para descarga
            session['predictions_data'] = unified_predictions.to_json()
            session['irrigation_data'] = irrigation_df.to_json()
            session['horizon_days'] = horizon_days
            
            print(f"✅ Predicción completada exitosamente")
            
            return render_template("prediction.html",
                                 plots=plots,
                                 prediction_summary=prediction_summary,
                                 table_data=table_data,
                                 show_results=True)
            
        except Exception as e:
            print(f"❌ Error en predicción: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f"Error al generar predicciones: {str(e)}", "danger")
            return redirect(url_for("main.prediccion"))
    
    # GET request - mostrar formulario
    return render_template("prediction.html", show_results=False)

@main.route("/descargar_predicciones")
@login_required
def descargar_predicciones():
    """Descargar predicciones como CSV"""
    try:
        if 'predictions_data' not in session or 'irrigation_data' not in session:
            flash("No hay datos de predicción para descargar.", "warning")
            return redirect(url_for("main.prediccion"))
        
        # Recuperar datos de la sesión
        predictions_df = pd.read_json(session['predictions_data'])
        irrigation_df = pd.read_json(session['irrigation_data'])
        horizon_days = session.get('horizon_days', 30)
        
        # Crear un Excel con dos hojas
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            predictions_df.to_excel(writer, sheet_name='Predicciones_Variables')
            irrigation_df.to_excel(writer, sheet_name='Calculo_Riego')
            
            # Añadir una hoja de resumen
            summary_df = pd.DataFrame([{
                'Total días predichos': horizon_days,
                'Riego total (mm)': irrigation_df['Riego_mm'].sum(),
                'Riego promedio (mm/día)': irrigation_df['Riego_mm'].mean(),
                'Riego máximo (mm/día)': irrigation_df['Riego_mm'].max(),
                'Riego mínimo (mm/día)': irrigation_df['Riego_mm'].min(),
                'Fecha generación': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }])
            summary_df.to_excel(writer, sheet_name='Resumen', index=False)
        
        output.seek(0)
        
        # Crear nombre de archivo
        fecha_descarga = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"predicciones_riego_{fecha_descarga}.xlsx"
        
        print(f"📥 Descargando archivo: {filename}")
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"❌ Error al descargar: {str(e)}")
        flash(f"Error al descargar: {str(e)}", "danger")
        return redirect(url_for("main.prediccion"))

@main.route("/api/predicciones_json")
@login_required
def predicciones_json():
    """API para obtener predicciones en formato JSON"""
    try:
        if 'predictions_data' not in session:
            return jsonify({"error": "No hay datos de predicción"}), 404
        
        predictions_df = pd.read_json(session['predictions_data'])
        irrigation_df = pd.read_json(session['irrigation_data'])
        horizon_days = session.get('horizon_days', 30)
        
        return jsonify({
            "predicciones": predictions_df.to_dict(orient='records'),
            "riego": irrigation_df.to_dict(orient='records'),
            "horizon_dias": horizon_days,
            "resumen": {
                "total_dias": horizon_days,
                "riego_total": float(irrigation_df['Riego_mm'].sum()),
                "riego_promedio": float(irrigation_df['Riego_mm'].mean()),
                "fecha_generacion": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/api/modelos_disponibles")
@login_required
def modelos_disponibles():
    """API para listar modelos disponibles"""
    try:
        models = load_all_models()
        return jsonify({
            "modelos": list(models.keys()),
            "total": len(models)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route("/entrenar_modelos")
@login_required
def entrenar_modelos():
    """Ruta para entrenar modelos (solo para desarrollo)"""
    try:
        from app.train_models import train_and_save
        train_and_save()
        flash("Modelos entrenados exitosamente", "success")
    except Exception as e:
        flash(f"Error entrenando modelos: {str(e)}", "danger")
    
    return redirect(url_for("main.prediccion"))