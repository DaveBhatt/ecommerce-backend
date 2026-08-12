class OrderNotFoundError(Exception):
    """Raised when the requested order does not exist."""

class EmptyCartError(Exception):
    """Raised when a user tries to checkout with an empty cart."""

