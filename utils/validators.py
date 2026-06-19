import re


def validate_amount(value) -> tuple[bool, str]:
    try:
        v = float(value)
        if v < 0:
            return False, "Amount cannot be negative."
        if v > 100_000:
            return False, "Amount seems too high — please verify."
        return True, ""
    except (ValueError, TypeError):
        return False, "Amount must be a valid number."


def validate_excitement_rating(value) -> tuple[bool, str]:
    try:
        v = int(float(value))
        if v < 1 or v > 5:
            return False, "Excitement rating must be between 1 and 5."
        return True, ""
    except (ValueError, TypeError):
        return False, "Excitement rating must be a number between 1 and 5."


def validate_food_item(value: str) -> tuple[bool, str]:
    v = (value or "").strip()
    if not v:
        return False, "Food item cannot be empty."
    if len(v) < 2:
        return False, "Food item name is too short (min 2 chars)."
    if len(v) > 200:
        return False, "Food item name is too long (max 200 chars)."
    return True, ""


def sanitize_text(value) -> str:
    """Strip control characters from text input."""
    if not isinstance(value, str):
        return str(value) if value is not None else ""
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    return cleaned.strip()


def validate_order(order: dict) -> tuple[bool, list[str]]:
    """
    Validate a complete order dict.
    Returns (is_valid, list_of_error_strings).
    """
    errors: list[str] = []

    ok, msg = validate_food_item(order.get("food_item", ""))
    if not ok:
        errors.append(f"Food Item: {msg}")

    if not order.get("platform"):
        errors.append("Platform: Please select a platform.")

    if not order.get("meal_type"):
        errors.append("Meal Type: Please select a meal type.")

    if not order.get("date"):
        errors.append("Date: Please select a date.")

    ok, msg = validate_amount(order.get("amount_paid", 0))
    if not ok:
        errors.append(f"Amount Paid: {msg}")

    if order.get("excitement_rating") not in (None, ""):
        ok, msg = validate_excitement_rating(order.get("excitement_rating"))
        if not ok:
            errors.append(f"Excitement Rating: {msg}")

    return len(errors) == 0, errors
