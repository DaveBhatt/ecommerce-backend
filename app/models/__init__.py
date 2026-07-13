from app.models.user import User
# This ensures Alembic can discover the model.

__all__ = ["User"]  # This line specifies that when you import * from this module, only the User class will be imported. It helps to control what is exposed when using wildcard imports.