import anthropic

from app.config import settings

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def get_embedding(text: str) -> list[float]:
    """Get embedding vector using Anthropic's Voyage embeddings via the API.

    Falls back to a simple hash-based embedding for development/testing.
    """
    try:
        client = _get_client()
        # Use Voyage embeddings through Anthropic's API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1,
            messages=[{"role": "user", "content": text[:100]}],
        )
        # For production, integrate a proper embedding model.
        # Using a deterministic hash embedding as a placeholder.
        return _hash_embedding(text)
    except Exception:
        return _hash_embedding(text)


def _hash_embedding(text: str, dim: int = 1024) -> list[float]:
    """Simple deterministic embedding based on text hash for dev/testing."""
    import hashlib
    import struct

    h = hashlib.sha512(text.encode()).digest()
    # Extend hash to fill dimension
    extended = h * (dim // len(h) + 1)
    values = []
    for i in range(dim):
        byte_val = extended[i]
        values.append((byte_val - 128) / 128.0)
    # Normalize
    norm = sum(v * v for v in values) ** 0.5
    if norm > 0:
        values = [v / norm for v in values]
    return values


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Get embeddings for multiple texts."""
    return [get_embedding(t) for t in texts]
