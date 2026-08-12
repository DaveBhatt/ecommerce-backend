class CartNotFoundError(Exception):
    """Raised when the user's cart does not exist."""

class CartItemNotFoundError(Exception):
    """Raised when a cart item does not exist."""