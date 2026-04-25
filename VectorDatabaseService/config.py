import os

# Milvus connection settings: fetches environment variables or uses default local hostnames
MILVUS_HOST = os.getenv("MILVUS_HOST", "standalone")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
MILVUS_URI  = f"http://{MILVUS_HOST}:{MILVUS_PORT}"

# Configuration for the visual embedding model used for image-related searches
EMBEDDING_MODEL_NAME = "clip-ViT-B-32"
EMBEDDING_DIM        = 512

# FastAPI/Uvicorn server settings
APP_HOST = "0.0.0.0"
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_NAME = "vector-database-service"

# Service Discovery: URL for the Eureka registry to allow microservices to find each other
EUREKA_SERVER = os.getenv("EUREKA_CLIENT_SERVICEURL_DEFAULTZONE", "http://eureka-server:8761/eureka")

# Indexing and search parameters (trade-off between speed and accuracy)
LAB_NLIST      = 64 # Number of clusters for the IVF index
LAB_NPROBE     = 16 # Number of clusters to search through during queries

# Ingestion settings for processing large datasets
BATCH_SIZE       = 64 # How many items to process at once to save memory
MAX_INGEST_COUNT = 44_446 # Maximum limit of rows to import

NLIST  = 256
NPROBE = 32

# Retrieval settings
DEFAULT_TOP_K    = 10
TWO_STAGE_RECALL = 50 # How many candidates to fetch before re-ranking

# Image processing limits to prevent network or memory hanging
IMAGE_DOWNLOAD_TIMEOUT = 10
MAX_IMAGE_SIZE_PX      = 1024

# LLM (Large Language Model) settings for RAG and generation tasks
OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")

# Library domain settings (books + book reviews)
BOOKS_COLLECTION          = "books"
BOOK_REVIEWS_COLLECTION   = "book_reviews"

BOOKS_EMBEDDING_MODEL     = "sentence-transformers/all-MiniLM-L6-v2"
BOOKS_EMBEDDING_DIM       = 384
BOOKS_NLIST               = 64
BOOKS_NPROBE              = 16
BOOKS_DEFAULT_TOP_K       = 5

REVIEWS_EMBEDDING_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"
REVIEWS_EMBEDDING_DIM     = 384
REVIEWS_NLIST             = 64
REVIEWS_NPROBE            = 16
REVIEWS_DEFAULT_TOP_K     = 5

# Minimum seed targets for assignment requirements
BOOKS_MIN_ROWS            = 200
REVIEWS_MIN_ROWS          = 200
REVIEWS_PER_BOOK          = 2
