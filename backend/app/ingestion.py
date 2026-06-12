import os  # Lets us set environment variables if needed
from pathlib import Path  # Helps work with file and folder paths

from langchain_core.documents import Document  # Stores text + metadata for RAG
from docling.document_converter import DocumentConverter  # Parses PDFs with structure awareness
from docling.chunking import HybridChunker  # Splits parsed PDFs into structure-aware chunks
from pypdf import PdfReader  # Fallback PDF reader if Docling model download fails

from langchain_openai import OpenAIEmbeddings  # Creates dense embeddings using OpenAI
from langchain_qdrant import QdrantVectorStore  # Stores vectors in Qdrant Cloud

from app.config import DATA_DIR  # Dataset folder path from .env
from app.config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION, HF_TOKEN  # API/settings from .env
from app.rbac import COLLECTION_ACCESS_ROLES  # Role access metadata for each collection


# Make Hugging Face token available to Docling if it tries to download models.
# This is optional. If Docling still fails, pypdf fallback will continue.
if HF_TOKEN:
    os.environ["HF_TOKEN"] = HF_TOKEN


# Main document collections in the MediBot dataset.
COLLECTIONS = ["general", "clinical", "nursing", "billing", "equipment"]


def load_markdown_file(file_path: Path, collection: str) -> list[Document]:
    """
    Load a Markdown file and convert it into one LangChain Document.
    """

    text = file_path.read_text(encoding="utf-8")

    return [
        Document(
            page_content=f"Section: {file_path.stem}\n\n{text}",
            metadata={
                "source_document": file_path.name,
                "collection": collection,
                "access_roles": COLLECTION_ACCESS_ROLES[collection],
                "section_title": file_path.stem,
                "chunk_type": "text",
                "chunk_index": 0,
                "parser": "markdown",
            },
        )
    ]


def split_text_into_chunks(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[str]:
    """
    Split long text into smaller overlapping chunks.
    This is used when Docling fails and we fall back to pypdf.
    """

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


def load_pdf_file_with_pypdf(file_path: Path, collection: str) -> list[Document]:
    """
    Fallback PDF loader using pypdf.
    This keeps the project moving if Docling cannot parse/download models.
    """

    print(f"Using pypdf fallback for: {file_path.name}")

    reader = PdfReader(str(file_path))
    full_text_parts = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        full_text_parts.append(f"\n\nPage {page_number}\n{page_text}")

    full_text = "\n".join(full_text_parts)
    text_chunks = split_text_into_chunks(full_text)

    docs = []

    for index, chunk_text in enumerate(text_chunks):
        docs.append(
            Document(
                page_content=f"Section: {file_path.stem}\n\n{chunk_text}",
                metadata={
                    "source_document": file_path.name,
                    "collection": collection,
                    "access_roles": COLLECTION_ACCESS_ROLES[collection],
                    "section_title": file_path.stem,
                    "chunk_type": "text",
                    "chunk_index": index,
                    "parser": "pypdf_fallback",
                },
            )
        )

    return docs


def load_pdf_file(file_path: Path, collection: str) -> list[Document]:
    """
    Try to parse PDF with Docling and HybridChunker.
    If Docling fails, fall back to pypdf.
    """

    try:
        print(f"Parsing PDF with Docling: {file_path.name}")

        converter = DocumentConverter()
        result = converter.convert(str(file_path))
        docling_document = result.document

        chunker = HybridChunker()
        chunks = list(chunker.chunk(docling_document))

        docs = []

        for index, chunk in enumerate(chunks):
            chunk_text = chunker.serialize(chunk=chunk)

            docs.append(
                Document(
                    page_content=chunk_text,
                    metadata={
                        "source_document": file_path.name,
                        "collection": collection,
                        "access_roles": COLLECTION_ACCESS_ROLES[collection],
                        "section_title": file_path.stem,
                        "chunk_type": "text",
                        "chunk_index": index,
                        "parser": "docling_hybridchunker",
                    },
                )
            )

        return docs

    except Exception as error:
        print(f"Docling failed for {file_path.name}")
        print(f"Reason: {error}")
        return load_pdf_file_with_pypdf(file_path, collection)


def build_documents() -> list[Document]:
    """
    Read all dataset files and convert them into LangChain Documents.
    """

    data_path = Path(DATA_DIR)
    all_docs = []

    print(f"DATA_DIR: {data_path}")
    print(f"Exists: {data_path.exists()}")

    for collection in COLLECTIONS:
        collection_path = data_path / collection

        if not collection_path.exists():
            print(f"Missing folder: {collection_path}")
            continue

        print(f"\nProcessing collection: {collection}")

        for file_path in collection_path.iterdir():
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() == ".md":
                print(f"Loading Markdown: {file_path.name}")
                docs = load_markdown_file(file_path, collection)

            elif file_path.suffix.lower() == ".pdf":
                docs = load_pdf_file(file_path, collection)

            else:
                print(f"Skipping unsupported file: {file_path.name}")
                continue

            all_docs.extend(docs)

    return all_docs


def test_build_documents():
    """
    Test function to confirm chunks and metadata are created correctly.
    """

    docs = build_documents()

    print(f"\nTotal LangChain documents created: {len(docs)}")

    for i, doc in enumerate(docs[:5], start=1):
        print(f"\n--- Document {i} ---")
        print("Content preview:")
        print(doc.page_content[:500])
        print("Metadata:")
        print(doc.metadata)


def index_documents_to_qdrant():
    """
    Build documents and store them in Qdrant Cloud using OpenAI embeddings.
    """

    docs = build_documents()

    print(f"\nTotal documents/chunks to index: {len(docs)}")

    dense_embeddings = OpenAIEmbeddings(
    model="text-embedding-ada-002"
    )

    QdrantVectorStore.from_documents(
        documents=docs,
        embedding=dense_embeddings,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=QDRANT_COLLECTION,
        force_recreate=True,
    )

    print(f"Indexed {len(docs)} chunks into Qdrant collection: {QDRANT_COLLECTION}")


if __name__ == "__main__":
    index_documents_to_qdrant()