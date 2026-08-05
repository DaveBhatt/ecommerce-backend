class ProductNotFoundError(Exception):
    """Raised when the requested product does not exist."""

class ProductInactiveError(Exception):
    """Raised when the requested product is inactive."""

class InsufficientStockError(Exception):
    """Raised when the requested quantity exceeds available stock."""