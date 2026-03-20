import io
import logging
from pathlib import Path

from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

LOCAL_STORAGE_DIR = Path("/app/uploads")


def upload_to_storage(file_bytes: bytes, destination_path: str) -> str:
    """Save uploaded PDF to local storage."""
    local_path = LOCAL_STORAGE_DIR / destination_path
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(file_bytes)
    logger.info(f"Saved to local storage: {local_path}")
    return f"local://{local_path}"


def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, int]:
    """Extract text from PDF using PyPDF2."""
    reader = PdfReader(io.BytesIO(file_bytes))
    all_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            all_text.append(text)
    return "\n".join(all_text), len(reader.pages)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[dict]:
    """Split text into overlapping chunks."""
    if not text.strip():
        return []

    chunks = []
    paragraphs = text.split("\n\n")
    current_chunk = ""
    chunk_index = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunks.append({"index": chunk_index, "content": current_chunk.strip()})
            chunk_index += 1
            # Keep overlap
            words = current_chunk.split()
            overlap_words = words[-overlap // 4 :] if len(words) > overlap // 4 else words
            current_chunk = " ".join(overlap_words) + "\n\n" + para
        else:
            current_chunk += ("\n\n" if current_chunk else "") + para

    if current_chunk.strip():
        chunks.append({"index": chunk_index, "content": current_chunk.strip()})

    return chunks
