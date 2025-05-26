from flask import Flask

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # Corrected imports
    from app.routes.dosham import dosham_bp
    from app.routes.horoscope import horoscope_bp
    from app.routes.status import status_bp

    # Register blueprints
    app.register_blueprint(dosham_bp, url_prefix="")
    app.register_blueprint(horoscope_bp, url_prefix="")
    app.register_blueprint(status_bp, url_prefix="")

    return app
