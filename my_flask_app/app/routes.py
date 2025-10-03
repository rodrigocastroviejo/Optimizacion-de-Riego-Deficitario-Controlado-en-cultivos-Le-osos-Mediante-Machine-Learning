from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models import Dataset
import os

main = Blueprint("main", __name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/upload", methods=["GET", "POST"])
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

            dataset = Dataset(filename=filename, filepath=upload_path)
            db.session.add(dataset)
            db.session.commit()

            flash("Archivo subido y registrado con éxito", "success")
            return redirect(url_for("main.upload_file"))
        else:
            flash("Formato no permitido. Solo CSV", "danger")
            return redirect(request.url)

    # Consultamos los datasets existentes y los pasamos al template
    datasets = Dataset.query.order_by(Dataset.uploaded_at.desc()).all()
    return render_template("upload.html", datasets=datasets)
