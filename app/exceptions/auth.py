class EmailAlreadyExistsError(Exception):
    """Raised when an email is already registered."""

class UsernameAlreadyExistsError(Exception):
    """Raised when a username is already registered."""

class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""