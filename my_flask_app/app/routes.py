# routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, send_file, session
from werkzeug.utils import secure_filename
from app import db
from app.models import Dataset, User
import os
from flask_login import login_user, logout_user, login_required, current_user

import pandas as pd
from datetime import datetime, timedelta
import io
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Importar el registro de clases personalizadas PRIMERO
from app.model_registry import register_custom_classes
register_custom_classes()

from app.progress_tracker import Progress_tracker

from app.auxiliary_prediction_functions import load_all_models, load_latest_data, make_predictions, unify_predictions, calculate_irrigation, create_prediction_plots

from app.train_models import train_and_save, Config

from app.state import PREDICTION_PROGRESS, PREDICTION_RESULTS



main = Blueprint("main", __name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}
MODELS_PATH = Path(__file__).resolve().parent / "models"


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
# RUTAS DE PREDICCIÓN
# ====================

@main.route("/prediccion", methods=["GET", "POST"])
@login_required
def prediccion():
    """Ruta principal de predicciones"""
    if request.method == "POST":
        # Redirigir a la página de progreso
        return render_template("prediction_progress.html")
    
    # GET request - mostrar formulario
    return render_template("prediction.html", show_results=False)


@main.route("/api/progreso_prediccion")
def api_progreso_prediccion():
    return jsonify(PREDICTION_PROGRESS.get('prediccion', {}))


@main.route("/prediccion/proceso", methods=["POST"])
@login_required
def prediccion_proceso():
            
    # Inicializar progreso
    progress_tracker = Progress_tracker("prediccion", 6)
   

    """Ruta para iniciar el proceso de predicción en segundo plano"""
    try:
        # Obtener parámetros
        horizon_days = int(request.form.get("horizon_days", 30))
        horizon_days = min(horizon_days, 365)

        # Ejecutar predicción (en la práctica, esto debería ser en un hilo separado)
        # Por simplicidad, lo hacemos sincrónico
        progress_tracker.update_progress(0, '🚀 Iniciando proceso de predicción...')
        

        # Paso 1: Cargar modelos
        models = load_all_models(progress_tracker)
        if not models:
            progress_tracker.update_progress(1, '❌ No se pudieron cargar modelos')
            progress_tracker.complete_progress()
            return jsonify({'error': 'No se encontraron modelos entrenados'}), 400
        

        # Paso 2: Cargar datos
        last_data = load_latest_data(progress_tracker)
        
        # Paso 3: Hacer predicciones
        predictions = make_predictions(models, last_data, horizon_days, progress_tracker)
        if not predictions:
            progress_tracker.update_progress(3, '❌ No se pudieron generar predicciones')
            progress_tracker.complete_progress()
            return jsonify({'error': 'No se pudieron generar predicciones'}), 400
        
        # Paso 4: Unificar predicciones
        unified_predictions = unify_predictions(predictions, horizon_days, progress_tracker)
        
        # Paso 5: Calcular riego
        irrigation_df = calculate_irrigation(unified_predictions, progress_tracker)
        
        # Paso 6: Crear gráficos
        plots = create_prediction_plots(unified_predictions, irrigation_df, last_data, progress_tracker)
        
        # Guardar resultados en sesión
        PREDICTION_RESULTS['predictions_data'] = unified_predictions.to_json()
        PREDICTION_RESULTS['irrigation_data'] = irrigation_df.to_json()
        PREDICTION_RESULTS['horizon_days'] = horizon_days
        PREDICTION_RESULTS['prediction_plots'] = plots
        
        # Completar progreso
        progress_tracker.update_progress(6, '✅ ¡Predicción completada exitosamente!')
        progress_tracker.complete_progress()
        
        return jsonify({
            'success': True,
            'redirect_url': url_for('main.prediccion_resultados')
        })
        
    except Exception as e:
        progress_tracker.update_progress(0, f'❌ Error en el proceso: {str(e)}')
        progress_tracker.complete_progress()
        return jsonify({'error': str(e)}), 500

@main.route("/prediccion/resultados")
@login_required
def prediccion_resultados():
    """Mostrar resultados de la predicción completada"""
    if 'predictions_data' not in PREDICTION_RESULTS:
        flash("No hay resultados de predicción disponibles", "warning")
        return redirect(url_for("main.prediccion"))
    
    try:
        # Cargar datos de la sesión
        unified_predictions = pd.read_json(PREDICTION_RESULTS['predictions_data'])
        irrigation_df = pd.read_json(PREDICTION_RESULTS['irrigation_data'])
        horizon_days = PREDICTION_RESULTS['horizon_days']
        plots = PREDICTION_RESULTS['prediction_plots']
        



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
        
        # Tomar las primeras 15 filas
        table_df = irrigation_df.head(15).copy()

        # Asegurarse de que 'Fecha' es datetime
        table_df['Fecha'] = pd.to_datetime(table_df['Fecha'])

        # Convertir a lista de diccionarios
        table_data = table_df.to_dict('records')

        
        return render_template("prediction.html",
                             plots=plots,
                             prediction_summary=prediction_summary,
                             table_data=table_data,
                             show_results=True)
        
    except Exception as e:
        flash(f"Error al cargar resultados: {str(e)}", "danger")
        return redirect(url_for("main.prediccion"))

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



# ======================
# RUTAS DE ENTRENAMIENTO
# ======================

@main.route("/entrenamiento", methods=["GET"])
@login_required
def entrenamiento():
    """Ruta principal de predicciones"""
    return render_template("training.html", show_results=False)

@main.route("/entrenamiento/progreso")
@login_required
def entrenamiento_progreso():
    """Página para monitorear el progreso del entrenamiento"""
    return render_template("train_progress.html")


@main.route("/api/progreso_entrenamiento")
@login_required
def api_progreso_entrenamiento():
    """API para obtener el progreso actual del entrenamiento"""
    return jsonify(PREDICTION_PROGRESS.get('entrenamiento', {}))

@main.route("/entrenamiento/proceso", methods=["POST"])
@login_required
def entrenamiento_proceso():
    """Ruta para iniciar el proceso de entrenamiento en segundo plano"""

    # Inicializar progreso
    progress_tracker = Progress_tracker("entrenamiento", 5)
    
    try:
        # Obtener parámetros del formulario
        data_filename = request.form.get("data_file")
        test_size = int(request.form.get("test_size", 180))
        
        # Modelos a entrenar
        models_to_train = {
            'sarima': 'sarima' in request.form.getlist("models"),
            'sarimax': 'sarimax' in request.form.getlist("models"),
            'var': 'var' in request.form.getlist("models"),
            'lstm': 'lstm' in request.form.getlist("models")
        }
        
        # Parámetros SARIMA
        sarima_p = int(request.form.get("sarima_p", 1))
        sarima_d = int(request.form.get("sarima_d", 1))
        sarima_q = int(request.form.get("sarima_q", 1))
        sarima_P = int(request.form.get("sarima_P", 1))
        sarima_D = int(request.form.get("sarima_D", 1))
        sarima_Q = int(request.form.get("sarima_Q", 1))
        sarima_s = int(request.form.get("sarima_s", 30))

        var_maxlags = int(request.form.get("var_maxlags", 15))

        
        # Verificar que se haya seleccionado al menos un modelo
        if not any(models_to_train.values()):
            return jsonify({'error': 'Selecciona al menos un tipo de modelo para entrenar'}), 400
        
        
        sarima_order = (sarima_p, sarima_d, sarima_q)
        sarima_seasonal_order = (sarima_p, sarima_d, sarima_q, sarima_s)

        # Crear configuración
        config = Config(
            data_filename,
            sarima_order,
            sarima_seasonal_order,
            var_maxlags,
            test_size
        )
        
        # Ejecutar entrenamiento (en la práctica, esto debería ser en un hilo separado)
        # Por simplicidad, lo hacemos sincrónico
        progress_tracker.update_progress(0, '🚀 Iniciando proceso de entrenamiento...')
        try:
            train_and_save(progress_tracker, config)
            flash("Modelos entrenados exitosamente", "success")
        except Exception as e:
            flash(f"Error entrenando modelos: {str(e)}", "danger")

        # Completar progreso
        progress_tracker.complete_progress()
        
        return jsonify({
            'success': True,
        })
        
    except Exception as e:
        progress_tracker.update_progress(5, f'❌ Error en el proceso: {str(e)}')
        progress_tracker.complete_progress()
        return jsonify({'error': str(e)}), 500


@main.route("/api/archivos_datos")
@login_required
def api_archivos_datos():
    """API para obtener archivos de datos disponibles"""
    
    uploads_dir = Path(current_app.config["UPLOAD_FOLDER"])
    print(uploads_dir)
    data_files = []
    
    if uploads_dir.exists():
        for file_path in uploads_dir.glob("*.csv"):
            try:
                # Leer información básica del archivo
                df = pd.read_csv(file_path, nrows=1)
                file_info = {
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'columns': df.columns.tolist(),
                    'rows': sum(1 for _ in open(file_path)) - 1  # Excluir encabezado
                }
                data_files.append(file_info)
            except Exception as e:
                print(f"Error leyendo {file_path}: {e}")
    
    return jsonify({'files': data_files})

@main.route("/api/modelos_disponibles")
@login_required
def api_modelos_disponibles():
    """API para listar modelos disponibles"""
    modelos = []
    
    if MODELS_PATH.exists():
        for file_path in MODELS_PATH.glob("*.pkl"):
            modelos.append(file_path.name)
    
    return jsonify({'modelos': modelos})
