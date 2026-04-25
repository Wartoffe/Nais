"""Milvus collection schema for book reviews (dense semantic retrieval)."""

from pymilvus import DataType, MilvusClient

from config import REVIEWS_EMBEDDING_DIM, REVIEWS_NLIST

REVIEWS_OUTPUT_FIELDS = [
    "review_id",
    "isbn",
    "book_id",
    "rating",
    "date_added",
    "n_votes",
    "user_type",
    "created_at",
    "review_text",
]


def reviews_schema(client: MilvusClient):
    """Defines the schema for the book_reviews collection."""
    schema = client.create_schema(auto_id=True, enable_dynamic_fields=False)

    schema.add_field("id", DataType.INT64, is_primary=True)
    schema.add_field("review_id", DataType.VARCHAR, max_length=64)
    schema.add_field("isbn", DataType.VARCHAR, max_length=32)
    schema.add_field("book_id", DataType.VARCHAR, max_length=64)
    schema.add_field("rating", DataType.INT16)
    schema.add_field("date_added", DataType.VARCHAR, max_length=64)
    schema.add_field("n_votes", DataType.INT32)
    schema.add_field("user_type", DataType.VARCHAR, max_length=32)
    schema.add_field("created_at", DataType.VARCHAR, max_length=64)
    schema.add_field("review_text", DataType.VARCHAR, max_length=4000)

    schema.add_field("review_embedding", DataType.FLOAT_VECTOR, dim=REVIEWS_EMBEDDING_DIM)

    return schema


def reviews_index_params(client: MilvusClient):
    """Defines scalar and dense indexes for book reviews."""
    idx = client.prepare_index_params()

    idx.add_index("id")
    idx.add_index("review_id", index_type="INVERTED")
    idx.add_index("isbn", index_type="INVERTED")
    idx.add_index("book_id", index_type="INVERTED")
    idx.add_index("rating", index_type="INVERTED")
    idx.add_index("date_added", index_type="INVERTED")
    idx.add_index("n_votes", index_type="INVERTED")
    idx.add_index("user_type", index_type="INVERTED")
    idx.add_index("created_at", index_type="INVERTED")

    idx.add_index(
        "review_embedding",
        index_type="IVF_FLAT",
        metric_type="COSINE",
        params={"nlist": REVIEWS_NLIST},
    )

    return idx
