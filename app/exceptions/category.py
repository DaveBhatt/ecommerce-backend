class CategoryAlreadyExistsError(Exception):
    """Raised when a category is already registered."""

class CategoryNotFoundError(Exception):
    """Raised when a category does not exists."""