"""Milvus collection schema for books (dense + sparse hybrid retrieval)."""

from pymilvus import DataType, Function, FunctionType, MilvusClient

from config import BOOKS_EMBEDDING_DIM, BOOKS_NLIST

BOOKS_OUTPUT_FIELDS = [
    "goodreads_id",
    "isbn",
    "title",
    "author",
    "coverImg",
    "pages",
    "has_image",
    "genre",
    "publisher",
    "year",
    "language",
    "description",
    "keywords_text",
]


def books_schema(client: MilvusClient):
    """Defines the schema for the books collection.

    Dense search is performed on dense_embedding.
    Sparse BM25 vectors are auto-generated from synthetic_document.
    """
    schema = client.create_schema(auto_id=True, enable_dynamic_fields=False)

    schema.add_field("id", DataType.INT64, is_primary=True)

    schema.add_field("goodreads_id", DataType.VARCHAR, max_length=32)
    schema.add_field("isbn", DataType.VARCHAR, max_length=32)
    schema.add_field("title", DataType.VARCHAR, max_length=512)
    schema.add_field("author", DataType.VARCHAR, max_length=256)
    schema.add_field("coverImg", DataType.VARCHAR, max_length=2048)
    schema.add_field("pages", DataType.INT32)
    schema.add_field("has_image", DataType.BOOL)
    schema.add_field("genre", DataType.VARCHAR, max_length=128)
    schema.add_field("publisher", DataType.VARCHAR, max_length=256)
    schema.add_field("year", DataType.INT32)
    schema.add_field("language", DataType.VARCHAR, max_length=32)
    schema.add_field("description", DataType.VARCHAR, max_length=4000)
    schema.add_field("keywords_text", DataType.VARCHAR, max_length=1024)

    schema.add_field(
        "synthetic_document",
        DataType.VARCHAR,
        max_length=6000,
        enable_analyzer=True,
        analyzer_params={"type": "english"},
        enable_match=True,
    )

    schema.add_field("dense_embedding", DataType.FLOAT_VECTOR, dim=BOOKS_EMBEDDING_DIM)
    schema.add_field("sparse", DataType.SPARSE_FLOAT_VECTOR, is_function_output=True)

    schema.add_function(
        Function(
            name="bm25_books",
            function_type=FunctionType.BM25,
            input_field_names=["synthetic_document"],
            output_field_names=["sparse"],
        )
    )

    return schema


def books_index_params(client: MilvusClient):
    """Defines scalar, dense, and sparse indexes for books."""
    idx = client.prepare_index_params()

    idx.add_index("id")
    idx.add_index("goodreads_id", index_type="INVERTED")
    idx.add_index("isbn", index_type="INVERTED")
    idx.add_index("pages", index_type="INVERTED")
    idx.add_index("has_image", index_type="INVERTED")
    idx.add_index("genre", index_type="INVERTED")
    idx.add_index("year", index_type="INVERTED")
    idx.add_index("language", index_type="INVERTED")
    idx.add_index("publisher", index_type="INVERTED")

    idx.add_index(
        "dense_embedding",
        index_type="IVF_FLAT",
        metric_type="COSINE",
        params={"nlist": BOOKS_NLIST},
    )

    idx.add_index(
        "sparse",
        index_type="SPARSE_INVERTED_INDEX",
        metric_type="BM25",
    )

    return idx
