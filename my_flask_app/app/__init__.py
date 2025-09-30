from flask import Flask

def create_app():
    app = Flask(__name__)

    # Configuración básica
    app.config.from_object("config")

    # Registro de rutas
    from .routes import main
    app.register_blueprint(main)

    return app
