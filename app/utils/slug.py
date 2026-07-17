from slugify import slugify

def generate_slug(text: str) -> str:
    """
    Generate a URL-friendly slug from text.
    
    Example: "Gaming Laptop" -> "gaming-laptop"
    
    """
    return slugify(text)

print(generate_slug("Gaming Laptop"))