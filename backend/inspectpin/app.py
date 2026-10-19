import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from .config import Settings
from .errors import ServiceError
from .job_manager import JobManager
from .pipeline import Services
from .routes import api
from .storage import Storage


def create_app(settings=None, services=None):
    settings = settings or Settings.from_env()
    settings.validate()
    app = Flask(__name__)
    app.config.update(SETTINGS=settings, MAX_CONTENT_LENGTH=max(settings.max_voice_bytes, settings.max_image_bytes, settings.vision_max_image_bytes))
    services = services or Services.create(settings)
    app.extensions["services"] = services
    app.extensions["jobs"] = JobManager(settings, Storage(settings.data_dir), services)
    app.register_blueprint(api)

    @app.errorhandler(ServiceError)
    def service_error(exc):
        return jsonify(error=exc.as_dict()), exc.status

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify(error={"code": "UPLOAD_TOO_LARGE" if exc.code == 413 else "HTTP_ERROR", "message": exc.name}), exc.code

    @app.errorhandler(Exception)
    def unexpected(exc):
        logging.getLogger("inspectpin").error("Unhandled request error type=%s", type(exc).__name__)
        return jsonify(error={"code": "INTERNAL_ERROR", "message": "Server could not complete request"}), 500

    @app.after_request
    def headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    return app
