import re


async def sanitize_query(query: str) -> str:
    """Qidiruv so'rovini Telegram tugmalari uchun xavfsiz ko'rinishga keltiradi."""
    sanitized_query = re.sub(r"\s+", " ", re.sub(r"[^\w\s-]", " ", query, flags=re.UNICODE)).strip()
    return sanitized_query[:120]
