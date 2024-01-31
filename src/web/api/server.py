import os
import time

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from config import Config
from logging import Logger

from werkzeug.exceptions import BadRequest, Unauthorized, InternalServerError, NotFound
from core.errors.api_errors import (
    InvalidUsageError,
    InvalidCredentialsError,
    ValidationError,
    NotFoundError,
    InternalServerError as CustomInternalServerError,
)
from core.views.response import APIErrorResponse

cors = CORS()
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()

logger = Logger(__name__)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    cors.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)

    @app.errorhandler(BadRequest)
    def handle_bad_request(e):
        return APIErrorResponse(
            error="Bad Request",
            description=str(e),
            error_type="BadRequest",
            status_code=400,
        )

    @jwt.expired_token_loader
    def handle_expired_token(jwt_header, jwt_payload):
        return APIErrorResponse(
            error="Token Expired",
            description="Token has expired",
            error_type="TokenExpired",
            status_code=401,
        )

    @app.errorhandler(Unauthorized)
    def handle_unauthorized(e):
        return APIErrorResponse(
            error="Unauthorized access detected",
            description=str(e),
            error_type="Unauthorized",
            status_code=401,
        )

    @app.errorhandler(InvalidUsageError)
    def handle_invalid_usage_error(e):
        return APIErrorResponse(
            error=e.error_message,
            description=e.description,
            error_type="InvalidUsage",
            status_code=400,
        )

    @app.errorhandler(InvalidCredentialsError)
    def handle_invalid_credentials_error(e):
        return APIErrorResponse(
            error=e.error_message,
            description=e.description,
            error_type="InvalidCredentials",
            status_code=401,
        )

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return APIErrorResponse(
            error=e.error_message,
            description=e.description,
            error_type="ValidationError",
            status_code=400,
        )

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(e):
        return APIErrorResponse(
            error=e.error_message,
            description=e.description,
            error_type="NotFound",
            status_code=404,
        )

    @app.errorhandler(InternalServerError)
    def handle_internal_server_error(e):
        return APIErrorResponse(
            error="Internal Server Error",
            description=str(e),
            error_type="InternalServerError",
            status_code=500,
        )

    @app.errorhandler(CustomInternalServerError)
    def handle_custom_internal_server_error(e):
        return APIErrorResponse(
            error=e.error_message,
            description=e.description,
            error_type="InternalServerError",
            status_code=500,
        )
        
    @app.errorhandler(NotFound)
    def handle_not_found_error(e):
        return APIErrorResponse(
            error="Not Found",
            description=str(e),
            error_type="NotFound",
            status_code=404,
        )

    return app
