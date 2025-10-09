from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models import Dataset, User
import os
from flask_login import login_user, logout_user, login_required, current_user

main = Blueprint("main", __name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route("/")
def index():
    return render_template("index.html")

# ---------- AUTH ----------
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

    # mostramos únicamente los datasets del usuario actual
    datasets = Dataset.query.filter_by(user_id=current_user.id).order_by(Dataset.uploaded_at.desc()).all()
    return render_template("upload.html", datasets=datasets)
