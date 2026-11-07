"""Smart Irrigation Advisor - Flask application factory."""
import os
from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object("config.Config")
    if test_config:
        app.config.update(test_config)

    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)

    from . import models, routes
    models.init_app(app)
    app.register_blueprint(routes.bp)
    return app
