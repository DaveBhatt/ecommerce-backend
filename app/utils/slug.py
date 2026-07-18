from slugify import slugify

def generate_slug(text: str) -> str:
    """
    Generate a URL-friendly slug from text.
    
    Example: "Gaming Laptop" -> "gaming-laptop"
    
    """
    return slugify(text)
