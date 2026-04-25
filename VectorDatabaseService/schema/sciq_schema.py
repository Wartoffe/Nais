"""
Milvus collection schema for the SciQ dataset (Hybrid Search: Dense + Sparse).

This schema implements BM25 full-text search alongside semantic dense embeddings.
"""

from pymilvus import DataType, Function, FunctionType, MilvusClient
from config import SCIQ_EMBEDDING_DIM, SCIQ_NLIST


def sciq_schema(client: MilvusClient):
    """
    Defines the schema for the SciQ collection, including automated BM25 function.
    """
    schema = client.create_schema(auto_id=True, enable_dynamic_fields=False)

    # --- Primary Key and Metadata ---
    schema.add_field("id",    DataType.INT64, is_primary=True)
    schema.add_field("doc_id", DataType.INT64)

    # --- Text Fields with Full-Text Search (Analyzer) Enabled ---
    schema.add_field(
        "support_text", DataType.VARCHAR, max_length=2000,
        enable_analyzer=True,
        analyzer_params={"type": "english"},
        enable_match=True,  # Enables Phrase Match / Keyword Match
    )
    schema.add_field(
        "question", DataType.VARCHAR, max_length=1000,
        enable_analyzer=True,
        analyzer_params={"type": "english"},
        enable_match=True,
    )
    schema.add_field("correct_answer", DataType.VARCHAR, max_length=500)
    schema.add_field("support_length", DataType.INT32)

    # --- Vector Fields ---
    # Dense embedding (e.g., MiniLM-L6-v2, 384-dim) for semantic similarity
    schema.add_field("text_embedding", DataType.FLOAT_VECTOR, dim=SCIQ_EMBEDDING_DIM)

    # Sparse vector (BM25) — auto-populated from support_text via the Function below
    schema.add_field("sparse", DataType.SPARSE_FLOAT_VECTOR, is_function_output=True)

    # --- Integrated Functions ---
    # BM25 function automatically converts support_text into sparse vectors during ingestion
    schema.add_function(Function(
        name="bm25",
        function_type=FunctionType.BM25,
        input_field_names=["support_text"],
        output_field_names=["sparse"],
    ))

    return schema


def sciq_index_params(client: MilvusClient):
    """
    Defines indexing strategies for metadata, dense vectors, and sparse vectors.
    """
    idx = client.prepare_index_params()
    
    # Metadata indexing
    idx.add_index("id")
    idx.add_index("doc_id",         index_type="INVERTED")
    idx.add_index("support_length", index_type="INVERTED")
    
    # Dense vector index (IVF_FLAT for balanced speed/accuracy)
    idx.add_index(
        "text_embedding",
        index_type="IVF_FLAT",
        metric_type="COSINE",
        params={"nlist": SCIQ_NLIST},
    )
    
    # Sparse vector index for traditional keyword/BM25 retrieval
    idx.add_index(
        "sparse",
        index_type="SPARSE_INVERTED_INDEX",
        metric_type="BM25",
    )
    
    return idx