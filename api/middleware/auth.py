"""
Auth Middleware - Twilio signature verification and request authentication
"""

import os
import hmac
import hashlib
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def verify_twilio_signature(
    signature: Optional[str],
    request_url: str,
    request_params: dict,
    auth_token: Optional[str] = None
) -> bool:
    """
    Verify Twilio request signature to prevent webhook spoofing.

    Args:
        signature: X-Twilio-Signature header value
        request_url: Full URL of the request
        request_params: POST parameters from the request
        auth_token: Twilio auth token (defaults to TWILIO_AUTH_TOKEN env)

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature:
        logger.warning("No Twilio signature provided")
        return False

    auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")

    if not auth_token:
        logger.error("Twilio auth token not configured")
        return False

    # Sort parameters alphabetically
    sorted_params = sorted(request_params.items())

    # Build signature string
    signature_string = ""
    for key, value in sorted_params:
        signature_string += key + value

    # Add URL to signature string
    signature_string += request_url

    # Compute HMAC-SHA1 signature
    expected_signature = base64.b64encode(
        hmac.new(
            auth_token.encode("utf-8"),
            signature_string.encode("utf-8"),
            hashlib.sha1
        ).digest()
    ).decode("utf-8")

    # Constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(signature, expected_signature)

    if not is_valid:
        logger.warning("Invalid Twilio signature")

    return is_valid


def verify_api_key(api_key: Optional[str], expected_key: Optional[str] = None) -> bool:
    """
    Verify API key for internal endpoints.

    Args:
        api_key: Provided API key
        expected_key: Expected API key (defaults from env)

    Returns:
        True if key matches, False otherwise
    """
    expected_key = expected_key or os.getenv("INTERNAL_API_KEY")

    if not expected_key:
        logger.error("Internal API key not configured")
        return False

    if not api_key:
        logger.warning("No API key provided")
        return False

    return hmac.compare_digest(api_key, expected_key)


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    """
    Extract Bearer token from Authorization header.

    Args:
        authorization_header: Full Authorization header value

    Returns:
        Token string or None
    """
    if not authorization_header:
        return None

    parts = authorization_header.split()

    if len(parts) != 2:
        logger.warning("Invalid authorization header format")
        return None

    scheme = parts[0].lower()
    if scheme != "bearer":
        logger.warning(f"Unknown authorization scheme: {scheme}")
        return None

    return parts[1]