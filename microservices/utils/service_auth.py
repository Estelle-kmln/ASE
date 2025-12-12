"""
Service-to-Service Authentication Utilities
Provides API key validation for inter-service communication
"""

import os
from flask import request, jsonify
from functools import wraps


def validate_service_api_key():
    """
    Validate the service API key from request headers.

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    service_api_key = request.headers.get("X-Service-API-Key")
    expected_key = os.getenv("SERVICE_API_KEY")

    if not expected_key:
        return False, "Service API key not configured"

    if not service_api_key:
        return False, "Service API key required"

    if service_api_key != expected_key:
        return False, "Invalid service API key"

    return True, None


def require_service_auth(f):
    """
    Decorator to require service API key authentication.
    Used for internal service-to-service endpoints.

    Usage:
        @app.route('/internal/endpoint')
        @require_service_auth
        def internal_endpoint():
            ...
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_valid, error = validate_service_api_key()

        if not is_valid:
            return (
                jsonify({"error": error or "Service authentication required"}),
                401,
            )

        return f(*args, **kwargs)

    return decorated_function


def get_service_api_key_header(service_name):
    """
    Get the service API key for making requests to other services.

    Args:
        service_name: Name of the target service (e.g., 'card-service')

    Returns:
        dict with headers including service API key
    """
    # Convert service name to environment variable format
    # e.g., 'card-service' -> 'CARD_SERVICE_API_KEY'
    env_var_name = f"{service_name.upper().replace('-', '_')}_API_KEY"
    api_key = os.getenv(env_var_name)

    headers = {}
    if api_key:
        headers["X-Service-API-Key"] = api_key

    return headers
