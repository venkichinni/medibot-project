from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType

from app.config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION


def create_indexes():
    """
    Create Qdrant payload indexes for metadata fields used in RBAC filtering.
    Qdrant needs indexes before filtering on these metadata keys.
    """

    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

    client.create_payload_index(
        collection_name=QDRANT_COLLECTION,
        field_name="metadata.collection",
        field_schema=PayloadSchemaType.KEYWORD,
    )

    client.create_payload_index(
        collection_name=QDRANT_COLLECTION,
        field_name="metadata.access_roles",
        field_schema=PayloadSchemaType.KEYWORD,
    )

    print("Qdrant payload indexes created successfully.")


if __name__ == "__main__":
    create_indexes()