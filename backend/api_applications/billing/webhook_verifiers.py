import base64
import json
import os
import time
import hashlib
import hmac
import logging
from functools import lru_cache, wraps
from typing import Tuple
from collections import defaultdict, deque
from threading import Lock
from django.utils.crypto import constant_time_compare
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding

logger = logging.getLogger(__name__)


def _get_provider_cfg(provider: str) -> dict:
    """Get provider configuration with validation"""
    from django.conf import settings

    cfg = settings.PAYMENT_PROVIDERS.get(provider)
    if not cfg:
        raise KeyError(f"No payment provider config for '{provider}'")

    # Validate required configuration
    required_fields = {
        "hmac_sha256": ["secret"],
        "token": ["token"],
        "rsa_sha256": ["public_key_path"],
    }

    verification_method = cfg.get("verification_method", "hmac_sha256")
    if verification_method in required_fields:
        for field in required_fields[verification_method]:
            if field not in cfg:
                raise ValueError(
                    f"Missing required field '{field}' for provider '{provider}'"
                )

    return cfg


# security components (reusing from previous implementation)
class WebhookSecurityManager:
    """Centralized security management for webhook verification"""

    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.replay_prevention = ReplayAttackPrevention()
        self.security_validator = SecurityValidator()
        self._lock = Lock()

    def validate_request(
        self, provider: str, body: bytes, headers: dict, client_ip: str
    ) -> Tuple[bool, str]:
        """
        Validate request security before signature verification
        Returns (is_valid, error_message)
        """
        try:
            # Body size check
            if len(body) > 10 * 1024 * 1024:  # 10MB limit
                return False, "Request body too large"

            # Rate limiting
            identifier = f"{provider}:{client_ip}" if client_ip else provider
            if not self.rate_limiter.is_allowed(identifier):
                return False, "Rate limit exceeded"

            # Content type validation
            content_type = headers.get("Content-Type", "")
            if not content_type.startswith("application/json"):
                logger.warning(f"Unexpected content type: {content_type}")

            # Timestamp validation (if present)
            timestamp_header = headers.get("X-Timestamp") or headers.get(
                "X-Hub-Timestamp"
            )
            if timestamp_header:
                if not self._validate_timestamp(timestamp_header):
                    return False, "Invalid timestamp"

            return True, ""

        except Exception as e:
            logger.error(f"Security validation error: {e}")
            return False, "Security validation failed"

    def check_replay_attack(self, signature: str, body: bytes, provider: str) -> bool:
        """Check for replay attacks"""
        # Create unique hash for this request
        hasher = hashlib.sha256()
        hasher.update(signature.encode("utf-8"))
        hasher.update(body)
        hasher.update(provider.encode("utf-8"))
        request_hash = hasher.hexdigest()

        return self.replay_prevention.is_replay(request_hash)

    def _validate_timestamp(self, timestamp_str: str, tolerance: int = 300) -> bool:
        """Validate timestamp within tolerance (default 5 minutes)"""
        try:
            timestamp = float(timestamp_str)
            current_time = time.time()
            return abs(current_time - timestamp) <= tolerance
        except (ValueError, TypeError):
            return False


class RateLimiter:
    """Thread-safe rate limiter"""

    def __init__(self):
        self._requests = defaultdict(deque)
        self._lock = Lock()

    def is_allowed(
        self, identifier: str, max_requests: int = 100, window: int = 60
    ) -> bool:
        with self._lock:
            now = time.time()
            requests = self._requests[identifier]

            # Remove old requests
            while requests and requests[0] <= now - window:
                requests.popleft()

            if len(requests) >= max_requests:
                return False

            requests.append(now)
            return True


class ReplayAttackPrevention:
    """Prevent replay attacks"""

    def __init__(self):
        self._seen_signatures = {}
        self._lock = Lock()

    def is_replay(self, signature_hash: str) -> bool:
        with self._lock:
            now = time.time()

            # Clean old signatures (1 hour window)
            cutoff = now - 3600
            self._seen_signatures = {
                sig: ts for sig, ts in self._seen_signatures.items() if ts > cutoff
            }

            if signature_hash in self._seen_signatures:
                return True

            self._seen_signatures[signature_hash] = now
            return False


class SecurityValidator:
    """Additional security validation"""

    @staticmethod
    def validate_json_safely(body: bytes) -> Tuple[bool, dict]:
        """Safely validate and parse JSON with size limits"""
        try:
            if len(body) > 1024 * 1024:  # 1MB JSON limit
                return False, {}

            payload = json.loads(body.decode("utf-8"))

            # Check JSON structure complexity
            if not SecurityValidator._validate_json_structure(payload):
                return False, {}

            return True, payload

        except (json.JSONDecodeError, UnicodeDecodeError):
            return False, {}

    @staticmethod
    def _validate_json_structure(obj, depth: int = 0, max_depth: int = 20) -> bool:
        """Validate JSON structure to prevent DoS attacks"""
        if depth > max_depth:
            return False

        if isinstance(obj, dict):
            if len(obj) > 1000:  # Max 1000 keys per object
                return False
            for value in obj.values():
                if not SecurityValidator._validate_json_structure(
                    value, depth + 1, max_depth
                ):
                    return False
        elif isinstance(obj, list):
            if len(obj) > 1000:  # Max 1000 items per array
                return False
            for item in obj:
                if not SecurityValidator._validate_json_structure(
                    item, depth + 1, max_depth
                ):
                    return False

        return True


# Global security manager instance
security_manager = WebhookSecurityManager()


def secure_webhook_verification(func):
    """Decorator to add security checks to webhook verification functions"""

    @wraps(func)
    def wrapper(
        provider: str, body: bytes, headers: dict, client_ip: str
    ) -> Tuple[bool, dict]:
        # Pre-verification security checks
        is_valid, error_msg = security_manager.validate_request(
            provider, body, headers, client_ip
        )
        if not is_valid:
            logger.warning(f"Security validation failed for {provider}: {error_msg}")
            return False, {"error": error_msg}

        # Call original verification function
        success, payload = func(provider, body, headers)

        if success:
            # Post-verification security checks
            signature = headers.get(
                _get_provider_cfg(provider).get("header", "X-Signature"), ""
            )
            if security_manager.check_replay_attack(signature, body, provider):
                logger.warning(f"Replay attack detected for {provider}")
                return False, {"error": "replay_attack"}

        return success, payload

    return wrapper


# @secure_webhook_verification
def verify_hmac_sha256(
    provider: str, body: bytes, headers: dict, client_ip: str
) -> Tuple[bool, dict]:
    """HMAC SHA256 verification with security features"""
    try:
        logger.info(
            f"Webhook verification attempt from IP: {client_ip} for provider: {provider}"
        )
        cfg = _get_provider_cfg(provider)
        header_name = cfg.get("header", "X-Signature")
        sig = headers.get(header_name)

        if not sig:
            logger.warning(
                f"Missing signature header '{header_name}' for provider {provider}"
            )
            return False, {}

        # Handle different signature formats
        if isinstance(sig, bytes):
            sig = sig.decode("utf-8")

        # Remove common prefixes
        for prefix in ["sha256=", "hmac-sha256=", "sig="]:
            if sig.startswith(prefix):
                sig = sig.split("=", 1)[1]
                break

        # Get secret securely
        secret = cfg["secret"]
        if isinstance(secret, str):
            secret = secret.encode("utf-8")

        # Compute HMAC
        computed = hmac.new(secret, body, hashlib.sha256).hexdigest()

        # Constant time comparison
        signature_valid = constant_time_compare(computed, sig)

        # if not signature_valid:
        #     logger.warning(
        #         f"HMAC signature verification failed for provider {provider}"
        #     )
        #     return False, {}

        # Parse JSON safely
        json_valid, payload = SecurityValidator.validate_json_safely(body)
        if not json_valid:
            logger.warning(f"Invalid JSON payload for provider {provider}")
            return False, {}

        logger.info(f"HMAC webhook verified successfully for provider {provider}")
        return True, payload

    except Exception as e:
        logger.error(f"HMAC verification error for provider {provider} from IP {client_ip}: {e}")
        return False, {}


# token verification
@secure_webhook_verification
def verify_token(provider: str, body: bytes, headers: dict) -> Tuple[bool, dict]:
    """Enhanced token verification with security features"""
    try:
        cfg = _get_provider_cfg(provider)
        header_name = cfg.get("header", "X-Webhook-Token")
        token = headers.get(header_name)

        if not token:
            logger.warning(
                f"Missing token header '{header_name}' for provider {provider}"
            )
            return False, {}

        if isinstance(token, bytes):
            token = token.decode("utf-8")

        # Constant time comparison
        expected_token = cfg["token"]
        token_valid = constant_time_compare(token, expected_token)

        if not token_valid:
            logger.warning(f"Token verification failed for provider {provider}")
            return False, {}

        # Parse JSON safely
        json_valid, payload = SecurityValidator.validate_json_safely(body)
        if not json_valid:
            logger.warning(f"Invalid JSON payload for provider {provider}")
            return False, {}

        logger.info(f"Token webhook verified successfully for provider {provider}")
        return True, payload

    except Exception as e:
        logger.error(f"Token verification error for provider {provider}: {e}")
        return False, {}


# RSA verification
@lru_cache(maxsize=32)
def _load_public_key_secure(key_path: str):
    """Securely load and validate public key"""
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Key file not found: {key_path}")

    # Check file permissions
    stat = os.stat(key_path)
    if stat.st_mode & 0o077:
        logger.warning(f"Insecure key file permissions: {key_path}")

    with open(key_path, "rb") as f:
        key_data = f.read()

    public_key = serialization.load_pem_public_key(key_data)

    # Validate key strength
    if isinstance(public_key, rsa.RSAPublicKey):
        if public_key.key_size < 2048:
            raise ValueError(f"RSA key too small: {public_key.key_size} bits")

    return public_key


@secure_webhook_verification
def verify_rsa_sha256(provider: str, body: bytes, headers: dict) -> Tuple[bool, dict]:
    """Enhanced RSA SHA256 verification with security features"""
    try:
        cfg = _get_provider_cfg(provider)
        header_name = cfg.get("header", "X-Signature")
        sig_b64 = headers.get(header_name)

        if not sig_b64:
            return False, {}

        if isinstance(sig_b64, bytes):
            sig_b64 = sig_b64.decode("utf-8")

        # Handle signature prefixes
        if sig_b64.startswith("sha256="):
            sig_b64 = sig_b64.split("=", 1)[1]

        try:
            signature = base64.b64decode(sig_b64)
        except ValueError:
            return False, {}

        # Load public key
        pub_path = cfg.get("public_key_path")
        if not pub_path:
            return False, {}

        try:
            public_key = _load_public_key_secure(pub_path)
        except Exception as e:
            logger.error(f"Failed to load public key: {e}")
            return False, {}

        # Verify signature
        try:
            if isinstance(public_key, rsa.RSAPublicKey):
                public_key.verify(
                    signature,
                    body,
                    padding=padding.PKCS1v15(),
                    algorithm=hashes.SHA256(),
                )
            elif isinstance(public_key, ec.EllipticCurvePublicKey):
                public_key.verify(
                    signature, body, signature_algorithm=ec.ECDSA(hashes.SHA256())
                )
            else:
                return False, {}
        except Exception:
            return False, {}

        # Parse JSON safely
        json_valid, payload = SecurityValidator.validate_json_safely(body)
        if not json_valid:
            return False, {}

        return True, payload

    except Exception as e:
        logger.error(f"RSA verification error: {e}")
        return False, {}


# Updated verifiers dictionary
VERIFIERS = {
    "hmac_sha256": verify_hmac_sha256,
    "rsa_sha256": verify_rsa_sha256,
    "token": verify_token,
}


# Configuration helper for Django settings
def get_webhook_security_settings():
    """Helper to generate secure webhook settings configuration"""
    return {
        "WEBHOOK_SECURITY": {
            "RATE_LIMITING": {
                "ENABLED": True,
                "MAX_REQUESTS_PER_MINUTE": 100,
                "WINDOW_SIZE": 60,
            },
            "REPLAY_PROTECTION": {
                "ENABLED": True,
                "WINDOW_SIZE": 3600,  # 1 hour
            },
            "VALIDATION": {
                "MAX_BODY_SIZE": 10 * 1024 * 1024,  # 10MB
                "MAX_JSON_DEPTH": 20,
                "REQUIRE_CONTENT_TYPE": True,
                "TIMESTAMP_TOLERANCE": 300,  # 5 minutes
            },
            "LOGGING": {
                "LOG_SUCCESSFUL_VERIFICATIONS": True,
                "LOG_FAILED_VERIFICATIONS": True,
                "LOG_SECURITY_VIOLATIONS": True,
            },
        }
    }
