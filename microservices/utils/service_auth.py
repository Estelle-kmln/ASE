"""
Service-to-Service Authentication Utility
Implements zero-trust networking principles for inter-service communication
"""

import os
import hmac
import hashlib
from functools import wraps
from flask import request, jsonify


class ServiceAuth:
    """Service-to-service authentication using API keys."""

    # Service API keys - loaded from environment variables
    SERVICE_KEYS = {
        "auth-service": os.getenv("AUTH_SERVICE_API_KEY", ""),
        "card-service": os.getenv("CARD_SERVICE_API_KEY", ""),
        "game-service": os.getenv("GAME_SERVICE_API_KEY", ""),
        "leaderboard-service": os.getenv("LEADERBOARD_SERVICE_API_KEY", ""),
        "logs-service": os.getenv("LOGS_SERVICE_API_KEY", ""),
        "api-gateway": os.getenv("API_GATEWAY_SERVICE_KEY", ""),
    }

    # Service name for this service instance
    CURRENT_SERVICE_NAME = os.getenv("SERVICE_NAME", "")

    @classmethod
    def get_service_key(cls, service_name: str) -> str:
        """Get API key for a service."""
        return cls.SERVICE_KEYS.get(service_name, "")

    @classmethod
    def validate_service_key(
        cls, provided_key: str, expected_service: str = None
    ) -> bool:
        """Validate a service API key."""
        if not provided_key:
            return False

        # If expected_service is specified, validate against that service's key
        if expected_service:
            expected_key = cls.SERVICE_KEYS.get(expected_service, "")
            if not expected_key:
                return False
            return hmac.compare_digest(provided_key, expected_key)

        # Otherwise, check if key matches any service key
        for service_name, key in cls.SERVICE_KEYS.items():
            if hmac.compare_digest(provided_key, key):
                return True

        return False

    @classmethod
    def get_service_from_key(cls, provided_key: str) -> str:
        """Identify which service a key belongs to."""
        for service_name, key in cls.SERVICE_KEYS.items():
            if hmac.compare_digest(provided_key, key):
                return service_name
        return None

    @classmethod
    def require_service_auth(cls, allowed_services: list = None):
        """
        Decorator to require service-to-service authentication.

        Args:
            allowed_services: List of service names allowed to call this endpoint.
                            If None, any authenticated service is allowed.
        """

        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Get service API key from header
                service_key = request.headers.get("X-Service-API-Key", "")

                if not service_key:
                    return (
                        jsonify(
                            {
                                "error": "Service authentication required",
                                "message": "Missing X-Service-API-Key header",
                            }
                        ),
                        401,
                    )

                # Validate the service key
                if not cls.validate_service_key(service_key):
                    return (
                        jsonify(
                            {
                                "error": "Invalid service credentials",
                                "message": "Service API key is invalid",
                            }
                        ),
                        403,
                    )

                # If specific services are allowed, check authorization
                if allowed_services:
                    calling_service = cls.get_service_from_key(service_key)
                    if calling_service not in allowed_services:
                        return (
                            jsonify(
                                {
                                    "error": "Service not authorized",
                                    "message": f"Service '{calling_service}' is not allowed to access this endpoint",
                                }
                            ),
                            403,
                        )

                return f(*args, **kwargs)

            return decorated_function

        return decorator

    @classmethod
    def make_service_request(
        cls,
        url: str,
        service_name: str,
        method: str = "GET",
        json_data: dict = None,
        headers: dict = None,
    ) -> dict:
        """
        Make an authenticated service-to-service request.

        Args:
            url: Target service URL
            service_name: Name of the calling service (to get its API key)
            method: HTTP method
            json_data: JSON payload for POST/PUT requests
            headers: Additional headers to include

        Returns:
            dict with 'success', 'status_code', and 'data' or 'error'
        """
        import requests

        # Get API key for the calling service
        api_key = cls.get_service_key(service_name)
        if not api_key:
            return {
                "success": False,
                "error": f"No API key configured for service: {service_name}",
            }

        # Prepare headers
        request_headers = {
            "X-Service-API-Key": api_key,
            "Content-Type": "application/json",
        }
        if headers:
            request_headers.update(headers)

        try:
            if method.upper() == "GET":
                response = requests.get(
                    url, headers=request_headers, timeout=10
                )
            elif method.upper() == "POST":
                response = requests.post(
                    url, headers=request_headers, json=json_data, timeout=10
                )
            elif method.upper() == "PUT":
                response = requests.put(
                    url, headers=request_headers, json=json_data, timeout=10
                )
            elif method.upper() == "DELETE":
                response = requests.delete(
                    url, headers=request_headers, timeout=10
                )
            else:
                return {
                    "success": False,
                    "error": f"Unsupported HTTP method: {method}",
                }

            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "data": (
                    response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else response.text
                ),
                "error": None if response.status_code < 400 else response.text,
            }
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
