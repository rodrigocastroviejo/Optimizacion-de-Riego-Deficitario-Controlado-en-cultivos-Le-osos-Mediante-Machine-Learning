from flask import Blueprint, render_template, request, redirect, url_for, flash
import os

main = Blueprint("main", __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        flash("No se envió ningún archivo")
        return redirect(url_for("main.index"))

    file = request.files["file"]

    if file.filename == "":
        flash("Archivo vacío")
        return redirect(url_for("main.index"))

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    flash(f"Archivo {file.filename} subido con éxito")

    # Aquí llamarías a tu validador/conversor
    # validate_dataset(filepath)

    return redirect(url_for("main.index"))
