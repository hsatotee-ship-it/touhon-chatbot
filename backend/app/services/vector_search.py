import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embedding import get_embedding


async def search_similar_chunks(
    db: AsyncSession,
    query: str,
    user_id: uuid.UUID,
    top_k: int = 5,
) -> list[dict]:
    """Search for similar document chunks using pgvector cosine similarity."""
    query_embedding = get_embedding(query)
    embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

    sql = text("""
        SELECT
            dc.id,
            dc.content,
            dc.chunk_index,
            dc.metadata,
            d.filename,
            d.id as document_id,
            1 - (dc.embedding <=> CAST(:embedding AS vector)) as similarity
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE d.user_id = :user_id
          AND d.status = 'completed'
          AND dc.embedding IS NOT NULL
        ORDER BY dc.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """)

    result = await db.execute(
        sql,
        {"embedding": embedding_str, "user_id": str(user_id), "top_k": top_k},
    )
    rows = result.fetchall()

    return [
        {
            "chunk_id": str(row.id),
            "content": row.content,
            "chunk_index": row.chunk_index,
            "filename": row.filename,
            "document_id": str(row.document_id),
            "similarity": float(row.similarity),
        }
        for row in rows
    ]
