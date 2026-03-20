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


def _ocr_pdf_with_tesseract(file_bytes: bytes) -> tuple[str, int]:
    """Extract text from scanned PDF using pytesseract + pdf2image."""
    from pdf2image import convert_from_bytes
    import pytesseract

    logger.info("Converting PDF pages to images for OCR")
    images = convert_from_bytes(file_bytes, dpi=300)
    logger.info(f"Converted {len(images)} pages to images")

    all_text = []
    for i, image in enumerate(images):
        text = pytesseract.image_to_string(image, lang="jpn+eng")
        if text.strip():
            all_text.append(text.strip())
            logger.info(f"OCR page {i+1}: extracted {len(text.strip())} chars")
        else:
            logger.warning(f"OCR page {i+1}: no text extracted")

    total_text = "\n".join(all_text)
    logger.info(f"OCR total: {len(total_text)} chars from {len(images)} pages")
    return total_text, len(images)


def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, int]:
    """Extract text from PDF. Uses PyPDF2 first, falls back to pytesseract OCR."""
    logger.info(f"Reading PDF ({len(file_bytes)} bytes)")
    reader = PdfReader(io.BytesIO(file_bytes))
    page_count = len(reader.pages)
    logger.info(f"PDF has {page_count} pages")

    all_text = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            all_text.append(text)
            logger.info(f"Page {i+1}: extracted {len(text)} chars")
        else:
            logger.warning(f"Page {i+1}: no text extracted (may be scanned image)")

    total_text = "\n".join(all_text)
    logger.info(f"PyPDF2 total: {len(total_text)} chars from {page_count} pages")

    # Fallback to pytesseract if PyPDF2 extracted little or no text
    if len(total_text.strip()) < 50:
        logger.info("PyPDF2 extracted insufficient text, falling back to pytesseract OCR")
        try:
            total_text, page_count = _ocr_pdf_with_tesseract(file_bytes)
        except Exception as e:
            logger.error(f"pytesseract OCR failed: {type(e).__name__}: {e}")

    return total_text, page_count


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
