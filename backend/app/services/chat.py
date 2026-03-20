import uuid

import anthropic

from app.config import settings

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


SYSTEM_PROMPT = """あなたは登記簿謄本（登記事項証明書）の専門アシスタントです。
不動産登記簿謄本および法人登記簿謄本（商業登記）を含む、あらゆる種類の日本の登記書類に対応しています。
ユーザーがアップロードした謄本の内容に基づいて質問に回答してください。

対応する書類の例：
- 不動産登記簿謄本（土地・建物の登記事項証明書）
- 法人登記簿謄本（商業・法人の登記事項証明書）
- 履歴事項全部証明書、現在事項全部証明書
- 閉鎖事項証明書

回答ルール：
1. 提供された謄本の情報のみに基づいて回答してください
2. 情報が見つからない場合は「アップロードされた謄本にその情報は見つかりませんでした」と回答してください
3. 回答には必ず出典（どの謄本のどの部分か）を明記してください
4. 専門用語は必要に応じて簡単な説明を添えてください
5. 回答は日本語で行ってください

以下は関連する謄本の内容です：
"""


def generate_answer(
    query: str,
    context_chunks: list[dict],
    chat_history: list[dict] | None = None,
) -> tuple[str, list[dict]]:
    """Generate an answer using Claude API with RAG context."""
    client = _get_client()

    # Build context from retrieved chunks
    context_parts = []
    sources = []
    for i, chunk in enumerate(context_chunks):
        context_parts.append(
            f"【出典{i + 1}: {chunk['filename']} (類似度: {chunk['similarity']:.2f})】\n{chunk['content']}"
        )
        sources.append(
            {
                "index": i + 1,
                "filename": chunk["filename"],
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "similarity": chunk["similarity"],
            }
        )

    context_text = "\n\n---\n\n".join(context_parts)
    system = SYSTEM_PROMPT + "\n" + context_text

    # Build message history
    messages = []
    if chat_history:
        for msg in chat_history[-10:]:  # Keep last 10 messages
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": query})

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system,
            messages=messages,
        )
        answer = response.content[0].text
    except anthropic.AuthenticationError:
        raise ValueError("ANTHROPIC_API_KEY が未設定または無効です")
    except anthropic.APIError as e:
        raise ValueError(f"Claude API エラー: {e.message}")

    return answer, sources
