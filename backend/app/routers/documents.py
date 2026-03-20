import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.dependencies import get_current_user
from app.models.schemas import DocumentDetail, DocumentResponse
from app.models.tables import Document, DocumentChunk, User
from app.services.embedding import get_embedding
from app.services.ocr import chunk_text, extract_text_from_pdf, upload_to_storage

router = APIRouter(prefix="/api/documents", tags=["documents"])


async def process_document(document_id: uuid.UUID, file_bytes: bytes):
    """Background task: OCR → chunk → embed → store."""
    async with AsyncSessionLocal() as db:
        doc = await db.get(Document, document_id)
        if not doc:
            return

        try:
            doc.status = "processing"
            await db.commit()

            # OCR
            ocr_text, page_count = extract_text_from_pdf(file_bytes)
            doc.ocr_text = ocr_text
            doc.page_count = page_count

            # Chunk
            chunks = chunk_text(ocr_text)

            # Embed and store
            for chunk_data in chunks:
                embedding = get_embedding(chunk_data["content"])
                db_chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=chunk_data["index"],
                    content=chunk_data["content"],
                    embedding=embedding,
                    metadata_={"page_estimate": chunk_data["index"]},
                )
                db.add(db_chunk)

            doc.status = "completed"
            doc.updated_at = datetime.utcnow()
            await db.commit()

        except Exception as e:
            doc.status = "failed"
            doc.updated_at = datetime.utcnow()
            await db.commit()
            raise


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDFファイルのみアップロード可能です")

    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="ファイルサイズは50MB以下にしてください")

    file_bytes = await file.read()
    doc_id = uuid.uuid4()
    gcs_path = f"documents/{user.id}/{doc_id}/{file.filename}"

    # Upload to storage
    gcs_uri = upload_to_storage(file_bytes, gcs_path)

    # Create DB record
    document = Document(
        id=doc_id,
        user_id=user.id,
        filename=file.filename,
        gcs_path=gcs_uri,
        status="pending",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Process in background
    background_tasks.add_task(process_document, doc_id, file_bytes)

    return DocumentResponse.model_validate(document)


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())
    )
    return [DocumentResponse.model_validate(d) for d in result.scalars().all()]


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = await db.get(Document, document_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(status_code=404, detail="ドキュメントが見つかりません")
    return DocumentDetail.model_validate(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = await db.get(Document, document_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(status_code=404, detail="ドキュメントが見つかりません")
    await db.delete(doc)
    await db.commit()
