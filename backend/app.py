import os
from pathlib import Path

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY_ENABLED", "False")
os.environ.setdefault("CHROMADB_TELEMETRY_ENABLED", "False")

from flask import Flask, jsonify

from config import Config
from extensions import cors, db, jwt
from routes.auth import auth_bp
from routes.chat import chat_bp
from routes.folders import folders_bp
from routes.materials import materials_bp
from routes.plans import plans_bp
from routes.stats import stats_bp
from routes.tasks import tasks_bp
from services.schema_service import ensure_schema_compatibility


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["CHROMA_DIR"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(folders_bp, url_prefix="/api/material-folders")
    app.register_blueprint(materials_bp, url_prefix="/api/materials")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(plans_bp, url_prefix="/api/plans")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(stats_bp, url_prefix="/api/stats")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "name": "Study-System"})

    if app.config["AUTO_CREATE_TABLES"]:
        with app.app_context():
            try:
                db.create_all()
                ensure_schema_compatibility(app)
            except Exception as exc:
                app.logger.warning("Database tables were not created automatically: %s", exc)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
