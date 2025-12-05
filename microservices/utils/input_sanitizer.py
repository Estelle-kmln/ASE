"""
Input Sanitization Utility
Centralized input validation and sanitization for all microservices
Protects against SQL injection, XSS, path traversal, and other injection attacks
"""

import re
import html
import uuid
import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote, unquote


class InputSanitizer:
    """Centralized input sanitization and validation class."""

    # Security patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(--|#|\/\*|\*\/)",
        r"(\bOR\b.*=.*|\bAND\b.*=.*)",  # Fixed: single = is enough
        r"(0x[0-9a-fA-F]+)",
        r"(\bCHAR\b|\bASCII\b|\bSUBSTRING\b)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$()]",
        r"\.\.\/",
        r"\/etc\/",
        r"\/proc\/",
        r"\/sys\/",
        r"cmd\.exe",
        r"powershell",
        r"bash",
        r"sh\s+",
    ]

    # Valid characters for different input types
    ALPHANUMERIC = re.compile(r"^[a-zA-Z0-9]+$")
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")
    UUID_PATTERN = re.compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )
    CARD_TYPE_PATTERN = re.compile(r"^(rock|paper|scissors)$", re.IGNORECASE)

    @staticmethod
    def sanitize_string(
        input_str: str, max_length: int = 255, allow_special: bool = False
    ) -> str:
        """
        Sanitize string input by removing dangerous characters.

        Args:
            input_str: Input string to sanitize
            max_length: Maximum allowed length
            allow_special: Whether to allow some special characters

        Returns:
            Sanitized string

        Raises:
            ValueError: If input contains dangerous patterns
        """
        if not isinstance(input_str, str):
            raise ValueError("Input must be a string")

        # Strip whitespace
        sanitized = input_str.strip()

        # Check length
        if len(sanitized) > max_length:
            raise ValueError(f"Input exceeds maximum length of {max_length}")

        # Check for SQL injection patterns
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                raise ValueError(
                    "Input contains potentially dangerous SQL patterns"
                )

        # Check for XSS patterns
        for pattern in InputSanitizer.XSS_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                raise ValueError(
                    "Input contains potentially dangerous XSS patterns"
                )

        # Check for command injection patterns
        for pattern in InputSanitizer.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                raise ValueError(
                    "Input contains potentially dangerous command injection patterns"
                )

        # HTML encode to prevent XSS
        sanitized = html.escape(sanitized)

        # Remove non-printable characters
        sanitized = "".join(
            char
            for char in sanitized
            if ord(char) >= 32 or char in ["\n", "\r", "\t"]
        )

        # If not allowing special characters, remove them
        if not allow_special:
            sanitized = re.sub(r'[<>&"\'`]', "", sanitized)

        return sanitized

    @staticmethod
    def validate_username(username: str) -> str:
        """
        Validate and sanitize username input.

        Args:
            username: Username to validate

        Returns:
            Sanitized username

        Raises:
            ValueError: If username is invalid
        """
        if not username:
            raise ValueError("Username cannot be empty")

        # Basic sanitization
        username = InputSanitizer.sanitize_string(
            username, max_length=50, allow_special=False
        )

        # Remove HTML entities that might have been added
        username = html.unescape(username)

        # Check format
        if not InputSanitizer.USERNAME_PATTERN.match(username):
            raise ValueError(
                "Username contains invalid characters. Only letters, numbers, dots, underscores, and hyphens allowed"
            )

        # Length check
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")

        return username  # Keep original case

    @staticmethod
    def validate_password(password: str) -> str:
        """
        Validate password input.

        Args:
            password: Password to validate

        Returns:
            Original password if valid (passwords are not modified)

        Raises:
            ValueError: If password is invalid
        """
        if not password:
            raise ValueError("Password cannot be empty")

        # Check length
        if len(password) < 4:
            raise ValueError("Password must be at least 4 characters long")

        if len(password) > 128:
            raise ValueError("Password is too long")

        # Check for dangerous patterns (but allow some special characters in passwords)
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, password, re.IGNORECASE):
                raise ValueError("Password contains invalid patterns")

        # Ensure it's valid UTF-8
        try:
            password.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("Password contains invalid characters")

        return password

    @staticmethod
    def validate_game_id(game_id: str) -> str:
        """
        Validate game ID (UUID format).

        Args:
            game_id: Game ID to validate

        Returns:
            Validated game ID

        Raises:
            ValueError: If game ID is invalid
        """
        if not game_id:
            raise ValueError("Game ID cannot be empty")

        # Strip whitespace
        game_id = game_id.strip()

        # Check UUID format
        if not InputSanitizer.UUID_PATTERN.match(game_id):
            raise ValueError("Invalid game ID format")

        return game_id.lower()

    @staticmethod
    def validate_card_type(card_type: str) -> str:
        """
        Validate card type input.

        Args:
            card_type: Card type to validate

        Returns:
            Validated card type

        Raises:
            ValueError: If card type is invalid
        """
        if not card_type:
            raise ValueError("Card type cannot be empty")

        # Strip and normalize
        card_type = card_type.strip().lower()

        # Check valid types
        if not InputSanitizer.CARD_TYPE_PATTERN.match(card_type):
            raise ValueError(
                "Invalid card type. Must be rock, paper, or scissors"
            )

        return card_type

    @staticmethod
    def validate_integer(
        value: Any, min_val: int = None, max_val: int = None
    ) -> int:
        """
        Validate integer input with bounds checking.

        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Validated integer

        Raises:
            ValueError: If value is invalid
        """
        # Check for string representations that would cause overflow
        if isinstance(value, str):
            # Reject extremely long numeric strings
            if len(value.strip()) > 20:  # Larger than max 64-bit integer
                raise ValueError("Integer value too large")

            # Check if it's a valid integer format (no decimals, spaces, etc.)
            value = value.strip()
            if not value or not re.match(r"^-?\d+$", value):
                raise ValueError("Invalid integer value")

        try:
            int_val = int(value)
        except (ValueError, TypeError, OverflowError):
            raise ValueError("Invalid integer value")

        # Additional check for extremely large values
        if abs(int_val) > 9223372036854775807:  # Max 64-bit signed integer
            raise ValueError("Integer value too large")

        if min_val is not None and int_val < min_val:
            raise ValueError(f"Value must be at least {min_val}")

        if max_val is not None and int_val > max_val:
            raise ValueError(f"Value must be at most {max_val}")

        return int_val

    @staticmethod
    def validate_json_payload(
        data: Dict[str, Any], required_fields: List[str] = None
    ) -> Dict[str, Any]:
        """
        Validate JSON payload structure.

        Args:
            data: JSON data to validate
            required_fields: List of required field names

        Returns:
            Validated data

        Raises:
            ValueError: If payload is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Payload must be a JSON object")

        # Check for required fields
        if required_fields:
            missing_fields = [
                field
                for field in required_fields
                if field not in data or data[field] is None
            ]
            if missing_fields:
                raise ValueError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )

        # Recursively sanitize string values
        def sanitize_recursive(obj):
            if isinstance(obj, dict):
                return {
                    key: sanitize_recursive(value) for key, value in obj.items()
                }
            elif isinstance(obj, list):
                return [sanitize_recursive(item) for item in obj]
            elif isinstance(obj, str):
                return InputSanitizer.sanitize_string(
                    obj, max_length=1000, allow_special=True
                )
            else:
                return obj

        return sanitize_recursive(data)

    @staticmethod
    def validate_query_parameter(
        param_name: str, param_value: str, param_type: str = "string"
    ) -> Any:
        """
        Validate query parameter.

        Args:
            param_name: Parameter name
            param_value: Parameter value
            param_type: Expected type (string, int, bool)

        Returns:
            Validated parameter value

        Raises:
            ValueError: If parameter is invalid
        """
        if param_value is None:
            return None

        if param_type == "string":
            return InputSanitizer.sanitize_string(param_value, max_length=100)
        elif param_type == "int":
            return InputSanitizer.validate_integer(param_value)
        elif param_type == "bool":
            if param_value.lower() in ["true", "1", "yes", "on"]:
                return True
            elif param_value.lower() in ["false", "0", "no", "off"]:
                return False
            else:
                raise ValueError(f"Invalid boolean value for {param_name}")
        else:
            raise ValueError(f"Unsupported parameter type: {param_type}")


class SecurityMiddleware:
    """Flask middleware for automatic input sanitization."""

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the security middleware with Flask app."""
        app.before_request(self.before_request)

    def before_request(self):
        """Process request before it reaches the route handler."""
        try:
            from flask import request, jsonify
        except ImportError:
            return None

        # Skip health check endpoints (check by path to avoid endpoint not being set yet)
        if request.path in [
            "/health",
            "/api/games/health",
            "/api/auth/health",
            "/api/cards/health",
            "/api/leaderboard/health",
        ]:
            return None

        # Validate Content-Type for POST/PUT requests (only if content is present)
        if request.method in ["POST", "PUT"]:
            # Only validate if there's actual content (content_length > 0)
            if request.content_length and request.content_length > 0:
                if (
                    not request.content_type
                    or "application/json" not in request.content_type
                ):
                    return (
                        jsonify(
                            {
                                "error": "Invalid Content-Type. Expected application/json"
                            }
                        ),
                        400,
                    )

        # Validate JSON payload size
        if (
            request.content_length and request.content_length > 1024 * 1024
        ):  # 1MB limit
            return jsonify({"error": "Payload too large"}), 413

        # Additional security headers can be added here
        return None


def require_sanitized_input(field_validations: Dict[str, str]):
    """
    Decorator for automatic input validation.

    Args:
        field_validations: Dictionary mapping field names to validation types
                          e.g., {'username': 'username', 'password': 'password', 'limit': 'int'}
    """

    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                from flask import request, jsonify
            except ImportError:
                return f(*args, **kwargs)

            try:
                # Validate JSON payload if present
                if request.is_json:
                    data = request.get_json()
                    if data:
                        for field, validation_type in field_validations.items():
                            if field in data:
                                if validation_type == "username":
                                    data[field] = (
                                        InputSanitizer.validate_username(
                                            data[field]
                                        )
                                    )
                                elif validation_type == "password":
                                    data[field] = (
                                        InputSanitizer.validate_password(
                                            data[field]
                                        )
                                    )
                                elif validation_type == "email":
                                    data[field] = InputSanitizer.validate_email(
                                        data[field]
                                    )
                                elif validation_type == "string":
                                    data[field] = (
                                        InputSanitizer.sanitize_string(
                                            data[field]
                                        )
                                    )
                                elif validation_type == "int":
                                    data[field] = (
                                        InputSanitizer.validate_integer(
                                            data[field]
                                        )
                                    )

                # Validate query parameters
                for param, validation_type in field_validations.items():
                    if param in request.args:
                        value = request.args.get(param)
                        if validation_type == "int":
                            InputSanitizer.validate_integer(value)
                        elif validation_type == "string":
                            InputSanitizer.sanitize_string(value)

                return f(*args, **kwargs)

            except ValueError as e:
                return (
                    jsonify({"error": f"Input validation failed: {str(e)}"}),
                    400,
                )

        wrapper.__name__ = f.__name__
        return wrapper

    return decorator
