from langchain_openai import OpenAIEmbeddings  # Uses same embedding model used during ingestion
from langchain_qdrant import QdrantVectorStore  # Connects LangChain to Qdrant
from langchain_groq import ChatGroq  # Connects to Groq LLM for final answer generation

from qdrant_client.models import Filter, FieldCondition, MatchAny  # Builds Qdrant metadata filters

from app.config import (
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    GROQ_API_KEY,
    GROQ_MODEL,
)
from app.rbac import get_collections_for_role  # Gets allowed collections for each role


def get_vectorstore():
    """
    Connect to the existing Qdrant collection.
    This does not recreate the collection; it only opens it for searching.
    """

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    vectorstore = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=QDRANT_COLLECTION,
    )

    return vectorstore


def build_rbac_filter(role: str) -> Filter:
    """
    Build a Qdrant filter so retrieval only searches collections allowed for the user role.
    This enforces RBAC inside Qdrant retrieval.
    """

    allowed_collections = get_collections_for_role(role)

    return Filter(
        must=[
            FieldCondition(
                key="metadata.collection",
                match=MatchAny(any=allowed_collections),
            )
        ]
    )


def keyword_boost_rerank(question: str, docs: list):
    """
    Simple local reranker.
    It boosts documents whose source filename, section title, or content
    contains important words from the question.
    """

    question_words = [
        word.lower().strip("?.!,")
        for word in question.split()
        if len(word) > 2
    ]

    scored_docs = []

    for doc in docs:
        metadata_text = " ".join(
            [
                doc.metadata.get("source_document", ""),
                doc.metadata.get("section_title", ""),
            ]
        ).lower()

        content_text = doc.page_content.lower()

        score = 0

        for word in question_words:
            if word in metadata_text:
                score += 5

            if word in content_text:
                score += 1

        scored_docs.append((score, doc))

    scored_docs.sort(key=lambda item: item[0], reverse=True)

    return [doc for score, doc in scored_docs]


def retrieve_documents(question: str, role: str, k: int = 50):
    """
    Retrieve relevant documents from Qdrant using role-based filtering.
    Then apply simple reranking and return the best 3 chunks.
    """

    allowed_collections = get_collections_for_role(role)

    if not allowed_collections:
        return []

    vectorstore = get_vectorstore()
    rbac_filter = build_rbac_filter(role)

    docs = vectorstore.similarity_search(
        query=question,
        k=k,
        filter=rbac_filter,
    )

    docs = keyword_boost_rerank(question, docs)

    return docs[:3]


def build_context(docs: list) -> str:
    """
    Convert retrieved documents into a context string for the LLM.
    """

    context_parts = []

    for i, doc in enumerate(docs, start=1):
        source_document = doc.metadata.get("source_document", "unknown")
        section_title = doc.metadata.get("section_title", "unknown")
        collection = doc.metadata.get("collection", "unknown")

        context_parts.append(
            f"""
Source {i}
Document: {source_document}
Section: {section_title}
Collection: {collection}
Content:
{doc.page_content}
"""
        )

    return "\n\n".join(context_parts)


def build_sources(docs: list) -> list[dict]:
    """
    Build source objects for API response.
    These sources will later be shown in the frontend.
    """

    sources = []

    for doc in docs:
        sources.append(
            {
                "source_document": doc.metadata.get("source_document", "unknown"),
                "section_title": doc.metadata.get("section_title", "unknown"),
                "collection": doc.metadata.get("collection", "unknown"),
            }
        )

    return sources


def answer_question(question: str, role: str) -> dict:
    """
    Full RAG function.
    1. Retrieve RBAC-filtered chunks from Qdrant.
    2. Send allowed context to Groq.
    3. Return answer and sources.
    """

    docs = retrieve_documents(question=question, role=role, k=50)

    if not docs:
        return {
            "answer": "I could not find any accessible information for your role.",
            "sources": [],
            "retrieval_type": "qdrant_rag",
            "role": role,
        }

    context = build_context(docs)

    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0,
    )

    prompt = f"""
You are MediBot, a role-aware assistant for MediAssist Health Network.

Answer the user's question using only the provided context.
Do not use outside knowledge.
If the answer is not present in the context, say:
"I could not find this information in the accessible documents."

User role:
{role}

Context:
{context}

Question:
{question}

Answer:
"""

    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "sources": build_sources(docs),
        "retrieval_type": "qdrant_rag",
        "role": role,
    }


def test_retrieval():
    """
    Quick test to confirm Qdrant retrieval and RBAC filtering work.
    """

    question = "What is the leave policy?"
    role = "nurse"

    docs = retrieve_documents(question=question, role=role, k=50)

    print(f"Question: {question}")
    print(f"Role: {role}")
    print(f"Retrieved documents: {len(docs)}")

    for i, doc in enumerate(docs, start=1):
        print(f"\n--- Result {i} ---")
        print(doc.page_content[:500])
        print(doc.metadata)


def test_answer():
    """
    Quick test to confirm full RAG answer generation works.
    """

    question = "What is the leave policy?"
    role = "nurse"

    result = answer_question(question=question, role=role)

    print(f"Question: {question}")
    print(f"Role: {role}")
    print("\nAnswer:")
    print(result["answer"])
    print("\nSources:")
    print(result["sources"])


if __name__ == "__main__":
    test_answer()