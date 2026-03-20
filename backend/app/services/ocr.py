import io
import logging
import os
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

LOCAL_STORAGE_DIR = Path("/app/uploads")


def _is_gcs_configured() -> bool:
    return bool(
        settings.gcs_bucket_name
        and settings.google_application_credentials
        and settings.google_application_credentials != "/path/to/service-account.json"
    )


def upload_to_gcs(file_bytes: bytes, destination_path: str) -> str:
    if _is_gcs_configured():
        from google.cloud import storage as gcs_storage

        client = gcs_storage.Client()
        bucket = client.bucket(settings.gcs_bucket_name)
        blob = bucket.blob(destination_path)
        blob.upload_from_string(file_bytes, content_type="application/pdf")
        return f"gs://{settings.gcs_bucket_name}/{destination_path}"

    # Local storage fallback
    local_path = LOCAL_STORAGE_DIR / destination_path
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(file_bytes)
    logger.info(f"Saved to local storage: {local_path}")
    return f"local://{local_path}"


def extract_text_from_pdf(file_bytes: bytes) -> tuple[str, int]:
    """Extract text from PDF. Uses Google Cloud Vision if configured, otherwise PyPDF2."""
    if _is_gcs_configured():
        from google.cloud import vision

        client = vision.ImageAnnotatorClient()
        input_config = vision.InputConfig(
            content=file_bytes,
            mime_type="application/pdf",
        )
        feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)
        request = vision.AnnotateFileRequest(
            input_config=input_config,
            features=[feature],
        )
        response = client.batch_annotate_files(requests=[request])

        all_text = []
        page_count = 0
        for file_response in response.responses:
            for page_response in file_response.responses:
                page_count += 1
                if page_response.full_text_annotation:
                    all_text.append(page_response.full_text_annotation.text)
        return "\n".join(all_text), page_count

    # PyPDF2 fallback
    from PyPDF2 import PdfReader

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
