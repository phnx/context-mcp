import re

# ============================================================================
# Input sanitization
# ============================================================================


def sanitize_user_id(user_id: str) -> str:
    """Allow only alphanumeric, underscore, hyphen"""
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", user_id).strip()
    if not sanitized:
        raise ValueError("User ID cannot be empty after sanitisation")
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    return sanitized


def sanitize_user_message(message: str, max_length: int = 5000) -> str:
    """Remove control characters and enforce length limits"""
    # Remove null bytes and control characters
    sanitized = "".join(char for char in message if ord(char) >= 32 or char in "\n\t")
    sanitized = sanitized.strip()

    if not sanitized:
        raise ValueError("Message cannot be empty")

    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def sanitize_tool_input(tool_input: dict) -> dict:
    """Basic sanitisation: trim strings, enforce length limits"""
    # NOTE should validate schema, but overkill for an example app

    sanitized = {}

    for param, value in tool_input.items():
        if isinstance(value, str):
            # Remove control chars, trim, limit length
            value = "".join(c for c in value if ord(c) >= 32 or c in "\n\t")
            value = value.strip()[:5000]

            if not value:
                raise ValueError(f"Parameter '{param}' cannot be empty")

            sanitized[param] = value

        elif isinstance(value, list):
            # sanitize list items (strings only)
            sanitized[param] = [_sanitize_string(item) for item in value]

        else:
            # Pass through numbers, bools, etc.
            sanitized[param] = value

    return sanitized


def _sanitize_string(value: str, max_length: int = 5000) -> str:
    """Helper: sanitize a single string"""
    value = "".join(c for c in value if ord(c) >= 32 or c in "\n\t")
    value = value.strip()[:max_length]

    if not value:
        raise ValueError("String value cannot be empty")

    return value
