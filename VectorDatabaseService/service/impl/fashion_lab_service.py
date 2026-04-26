import logging

from model.fashion_product import FashionProductBase
from repository.fashion_lab_repository import fashion_lab_repository
from service.i_fashion_lab_service import IFashionLabService
from services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


def _sanitize_string(value: str) -> str:
    """Escapes backslashes and quotes in filter expressions to prevent injection attacks."""
    if not isinstance(value, str):
        return str(value)
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _build_filter_expression(gender=None, colour=None, category=None) -> str:
    """
    Builds a Milvus filter expression using sanitized values.
    Combines conditions using the AND operator.
    """
    parts = []
    if gender:
        parts.append(f'gender == "{_sanitize_string(gender)}"')
    if colour:
        parts.append(f'base_colour == "{_sanitize_string(colour)}"')
    if category:
        parts.append(f'master_category == "{_sanitize_string(category)}"')
    return " && ".join(parts) if parts else ""


class FashionLabService(IFashionLabService):

    def create_product(self, product: FashionProductBase) -> dict:
        """
        Encodes the product name using the CLIP text tower; image_embedding = zero vector.
        Validates the input data before insertion.
        """
        if not product.product_name or not product.product_name.strip():
            raise ValueError("Product name cannot be empty")
        
        text_emb = embedding_service.encode_text_one(product.product_name)
        zero = embedding_service.zero_vector()
        
        record = {
            "product_id": 0,
            "product_name": product.product_name[:511],
            "gender": product.gender[:31] if product.gender else "",
            "master_category": product.master_category[:63] if product.master_category else "",
            "sub_category": product.sub_category[:63] if product.sub_category else "",
            "article_type": product.article_type[:63] if product.article_type else "",
            "base_colour": product.base_colour[:63] if product.base_colour else "",
            "season": product.season[:31] if product.season else "",
            "year": product.year if product.year else 0,
            "usage": product.usage[:63] if product.usage else "",
            "has_image": False,
            "text_embedding": text_emb,
            "image_embedding": zero,
        }
        
        result = fashion_lab_repository.insert([record])
        return {
            "inserted_ids": result.get("ids", []),
            "insert_count": result.get("insert_count", 0)
        }

    def list_products(self, gender, colour, category, limit, offset) -> list[dict]:
        """
        Clean scalar search — without vector ranking.
        Uses sanitized filter expressions.
        """
        if limit <= 0:
            raise ValueError("Limit must be positive")
        if offset < 0:
            raise ValueError("Offset cannot be negative")
        
        filter_expr = _build_filter_expression(gender, colour, category)
        
        return fashion_lab_repository.find_all(
            filter_expr=filter_expr, limit=limit, offset=offset,
        )

    def get_product(self, product_id: int) -> dict:
        """Retrieves a product by its ID with validation."""
        if product_id <= 0:
            raise ValueError("Product ID must be positive")
        
        row = fashion_lab_repository.find_by_id(product_id)
        if row is None:
            raise KeyError(f"Product {product_id} not found")
        return row

    def delete_product(self, product_id: int) -> dict:
        """Deletes a product by its ID with validation."""
        if product_id <= 0:
            raise ValueError("Product ID must be positive")
        
        result = fashion_lab_repository.delete_by_id(product_id)
        return {
            "deleted_id": product_id,
            "delete_count": result.get("delete_count", 0)
        }

    def text_search(self, query: str, top_k: int) -> list[dict]:
        """
        ANN (Approximate Nearest Neighbor) search: encodes text and searches text_embedding field.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        
        qvec = embedding_service.encode_text_one(query)
        return fashion_lab_repository.search([qvec], "text_embedding", top_k=top_k)[0]

    def filtered_search(self, query, gender, colour, category, top_k) -> list[dict]:
        """
        Pre-filtered ANN search: scalar 'WHERE' clause is applied before vector search.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        
        filter_expr = _build_filter_expression(gender, colour, category)
        qvec = embedding_service.encode_text_one(query)
        
        return fashion_lab_repository.search(
            [qvec], "text_embedding", top_k=top_k, filter_expr=filter_expr,
        )[0]

    def image_search(self, url: str, top_k: int) -> list[dict]:
        """
        Fetches an image from a URL, encodes with CLIP image tower, and searches image_embedding.
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        try:
            img = embedding_service.image_from_url(url)
            qvec = embedding_service.encode_image_one(img)
        except Exception as exc:
            logger.error(f"Failed to fetch/encode image from {url}: {exc}")
            raise ValueError(f"Cannot fetch/encode image: {exc}")

        return fashion_lab_repository.search([qvec], "image_embedding", top_k=top_k)[0]

    def image_search_from_pil(self, img, top_k: int) -> list[dict]:
        """Same as image_search but accepts a PIL image object directly."""
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        qvec = embedding_service.encode_image_one(img)
        return fashion_lab_repository.search([qvec], "image_embedding", top_k=top_k)[0]

    def text_to_image_search(self, query: str, top_k: int) -> list[dict]:
        """
        Cross-modal search: uses text vector to search the image_embedding space.
        Works because CLIP creates a shared embedding space for text and images.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        
        qvec = embedding_service.encode_text_one(query)
        return fashion_lab_repository.search([qvec], "image_embedding", top_k=top_k)[0]

    def image_to_text_search(self, url: str, top_k: int) -> list[dict]:
        """
        Reverse cross-modal: uses image vector to search the text_embedding space.
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        try:
            img = embedding_service.image_from_url(url)
            qvec = embedding_service.encode_image_one(img)
        except Exception as exc:
            logger.error(f"Failed to fetch/encode image from {url}: {exc}")
            raise ValueError(f"Cannot fetch/encode image: {exc}")

        return fashion_lab_repository.search([qvec], "text_embedding", top_k=top_k)[0]

    def image_to_text_search_from_pil(self, img, top_k: int) -> list[dict]:
        """Same as image_to_text_search but accepts a PIL image object directly."""
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        qvec = embedding_service.encode_image_one(img)
        return fashion_lab_repository.search([qvec], "text_embedding", top_k=top_k)[0]

    def multimodal_search_from_pil(self, text: str, img, text_weight: float, top_k: int) -> list[dict]:
        """Same as multimodal_search but accepts a PIL image object directly instead of a URL."""
        if not text or not text.strip():
            raise ValueError("Text query cannot be empty")
        if not 0.0 <= text_weight <= 1.0:
            raise ValueError("text_weight must be between 0.0 and 1.0")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        text_vec = embedding_service.encode_text_one(text)
        img_vec = embedding_service.encode_image_one(img)
        image_weight = 1.0 - text_weight
        recall_k = top_k * 2

        text_hits = fashion_lab_repository.search([text_vec], "text_embedding", top_k=recall_k)[0]
        image_hits = fashion_lab_repository.search([img_vec], "image_embedding", top_k=recall_k)[0]

        rrf_k = 60
        scores: dict[int, dict] = {}
        for rank, hit in enumerate(text_hits, start=1):
            doc_id = hit["id"]
            if doc_id not in scores:
                scores[doc_id] = {"data": hit, "fused": 0.0}
            scores[doc_id]["fused"] += text_weight / (rank + rrf_k)
        for rank, hit in enumerate(image_hits, start=1):
            doc_id = hit["id"]
            if doc_id not in scores:
                scores[doc_id] = {"data": hit, "fused": 0.0}
            scores[doc_id]["fused"] += image_weight / (rank + rrf_k)

        ranked = sorted(scores.values(), key=lambda x: x["fused"], reverse=True)
        results = []
        for item in ranked[:top_k]:
            row = dict(item["data"])
            row["fused_score"] = round(item["fused"], 6)
            results.append(row)
        return results

    def multimodal_search(self, text, image_url, text_weight, top_k) -> list[dict]:
        """Performs two independent ANN searches and merges them using Reciprocal Rank Fusion (RRF)."""
        if not text or not text.strip():
            raise ValueError("Text query cannot be empty")
        if not image_url or not image_url.strip():
            raise ValueError("Image URL cannot be empty")
        if not 0.0 <= text_weight <= 1.0:
            raise ValueError("text_weight must be between 0.0 and 1.0")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        text_vec = embedding_service.encode_text_one(text)

        try:
            img = embedding_service.image_from_url(image_url)
            img_vec = embedding_service.encode_image_one(img)
        except Exception as exc:
            logger.error(f"Failed to fetch/encode image from {image_url}: {exc}")
            raise ValueError(f"Cannot fetch/encode image: {exc}")

        image_weight = 1.0 - text_weight
        recall_k = top_k * 2

        text_hits = fashion_lab_repository.search(
            [text_vec], "text_embedding", top_k=recall_k
        )[0]
        image_hits = fashion_lab_repository.search(
            [img_vec], "image_embedding", top_k=recall_k
        )[0]

        rrf_k = 60
        scores: dict[int, dict] = {}

        for rank, hit in enumerate(text_hits, start=1):
            doc_id = hit["id"]
            rrf_score = text_weight / (rank + rrf_k)
            if doc_id not in scores:
                scores[doc_id] = {"data": hit, "fused": 0.0}
            scores[doc_id]["fused"] += rrf_score

        for rank, hit in enumerate(image_hits, start=1):
            doc_id = hit["id"]
            rrf_score = image_weight / (rank + rrf_k)
            if doc_id not in scores:
                scores[doc_id] = {"data": hit, "fused": 0.0}
            else:
                for key, value in hit.items():
                    if key not in scores[doc_id]["data"] or key == "id":
                        scores[doc_id]["data"][key] = value
            scores[doc_id]["fused"] += rrf_score

        ranked = sorted(scores.values(), key=lambda x: x["fused"], reverse=True)

        results = []
        for item in ranked[:top_k]:
            row = dict(item["data"])
            row["fused_score"] = round(item["fused"], 6)
            results.append(row)

        return results

    def search_paginated(self, query: str, page: int, page_size: int) -> dict:
        """Standard ANN search with offset-based pagination."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if page < 1:
            raise ValueError("page must be >= 1")
        if page_size < 1 or page_size > 50:
            raise ValueError("page_size must be between 1 and 50")
        offset = (page - 1) * page_size
        if offset + page_size > 16384:
            raise ValueError("offset + page_size must be < 16384 (Milvus limit)")
        qvec = embedding_service.encode_text_one(query)
        results = fashion_lab_repository.search_with_offset(
            [qvec], "text_embedding", top_k=page_size, offset=offset,
        )[0]
        return {"query": query, "page": page, "page_size": page_size, "results": results}

    def search_with_iterator(self, query: str, batch_size: int) -> dict:
        """
        Iterative search that moves through results in batch steps.
        Simulates a search cursor to retrieve a large number of matches.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if batch_size < 1 or batch_size > 100:
            raise ValueError("batch_size must be between 1 and 100")
        qvec = embedding_service.encode_text_one(query)
        all_results, offset, batches = [], 0, 0
        while True:
            batch = fashion_lab_repository.search_with_offset(
                [qvec], "text_embedding", top_k=batch_size, offset=offset,
            )[0]
            if not batch:
                break
            all_results.extend(batch)
            offset += batch_size
            batches += 1
            if offset >= 1000:
                break
        return {
            "query":      query,
            "batch_size": batch_size,
            "batches":    batches,
            "total":      len(all_results),
            "results":    all_results,
        }

    def grouped_search(self, query: str, group_by_field: str, group_size: int, top_k: int) -> list[dict]:
        """
        Grouped Search: returns a maximum of 'group_size' results per distinct field value.
        Ensures category diversity in the results (e.g., don't show only black t-shirts).
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        valid_fields = {"gender", "master_category", "article_type", "base_colour", "season"}
        if group_by_field not in valid_fields:
            raise ValueError(f"group_by_field must be one of: {valid_fields}")
        qvec = embedding_service.encode_text_one(query)
        return fashion_lab_repository.search_grouped(
            [qvec], "text_embedding", top_k=top_k,
            group_by_field=group_by_field, group_size=group_size,
        )[0]

    def range_search(self, query: str, min_score: float, max_score: float) -> list[dict]:
        """
        Native Milvus range search — returns results whose COSINE score
        is within the range [min_score, max_score].
        Difference from /search/by-threshold: filter is executed INSIDE Milvus,
        not in Python, and can utilize all indexed results.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if not 0.0 <= min_score <= max_score <= 1.0:
            raise ValueError("Must satisfy 0 <= min_score <= max_score <= 1")
        qvec = embedding_service.encode_text_one(query)
        return fashion_lab_repository.search_range(
            [qvec], "text_embedding", radius=min_score, range_filter=max_score,
        )[0]

    def search_with_consistency(self, query: str, consistency_level: str, top_k: int) -> list[dict]:
        """Executes search with a specified consistency level (e.g., 'Strong' for immediate visibility)."""
        valid = {"Strong", "Session", "Bounded", "Eventually"}
        if consistency_level not in valid:
            raise ValueError(f"consistency_level must be one of: {valid}")
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        qvec = embedding_service.encode_text_one(query)
        return fashion_lab_repository.search_with_consistency(
            [qvec], "text_embedding", top_k, consistency_level,
        )[0]

    def hybrid_search_weighted(self, query: str, text_weight: float, top_k: int) -> list[dict]:
        """
        Hybrid search using WeightedRanker.
        Difference from RRFRanker:
          - WeightedRanker: Weights are applied directly to the similarity scores.
          - RRFRanker: Weights are applied to the ranks (more robust for different score scales).
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if not 0.0 <= text_weight <= 1.0:
            raise ValueError("text_weight must be between 0.0 and 1.0")
        qvec = embedding_service.encode_text_one(query)
        return fashion_lab_repository.hybrid_search_weighted(
            qvec, top_k, text_weight, round(1.0 - text_weight, 4),
        )

    def batch_text_search(self, queries: list[str], top_k: int) -> list[dict]:
        """
        Batch Search: Encodes all queries simultaneously and searches in a single 
        Milvus call. This is more efficient than N separate search requests.
        """
        if not queries:
            raise ValueError("Queries list cannot be empty")
        if len(queries) > 10:
            raise ValueError("Maximum 10 queries per batch")
        query_vecs = embedding_service.encode_text(queries)
        raw_results = fashion_lab_repository.search(query_vecs, "text_embedding", top_k=top_k)
        return [{"query": q, "matches": matches} for q, matches in zip(queries, raw_results)]

    def search_template_filter(
        self, query: str, min_year: int, colors: list[str], top_k: int,
    ) -> dict:
        """
        Search with Template Filters: Uses parameterized conditions that can be 
        easily modified without manual string reconstruction.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        sanitized = [_sanitize_string(c) for c in colors]
        color_list = ", ".join(f'"{c}"' for c in sanitized)
        filter_expr = f'year >= {min_year} && base_colour in [{color_list}]'
        qvec = embedding_service.encode_text_one(query)
        results = fashion_lab_repository.search(
            [qvec], "text_embedding", top_k=top_k, filter_expr=filter_expr,
        )[0]
        return {"filter_expr": filter_expr, "results": results}

    def search_in_partition(self, query: str, partition: str, top_k: int) -> dict:
        """
        Search within specific partitions.
        A partition limits the search to a subset of data — faster for large collections.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        qvec = embedding_service.encode_text_one(query)
        try:
            results = fashion_lab_repository.search_in_partition(
                [qvec], "text_embedding", top_k, [partition],
            )[0]
            return {"partition": partition, "results": results}
        except Exception as exc:
            raise ValueError(
                f"Partition '{partition}' not found. "
                f"Available: _default. Create partitions at collection level. Error: {exc}"
            )

    def products_by_year_range(self, min_year: int, max_year: int, limit: int) -> list[dict]:
        """""Numeric range query: filters items where year is between min and max."""
        if min_year > max_year:
            raise ValueError("min_year must be <= max_year")
        filter_expr = f"year >= {min_year} && year <= {max_year}"
        return fashion_lab_repository.find_all(filter_expr=filter_expr, limit=limit)

    def products_by_name_pattern(self, pattern: str, limit: int) -> list[dict]:
        """LIKE search by product_name — supports % as a wildcard."""
        if not pattern:
            raise ValueError("Pattern cannot be empty")
        safe = _sanitize_string(pattern)
        return fashion_lab_repository.find_all(
            filter_expr=f'product_name like "%{safe}%"', limit=limit,
        )

    def products_without_images(self, limit: int) -> list[dict]:
        """Returns products where has_image == false (no embedded image)."""
        return fashion_lab_repository.find_all(
            filter_expr="has_image == false", limit=limit,
        )

    def products_in_colors(self, colors: list[str], limit: int) -> list[dict]:
        """IN operator — returns products whose color is in the specified list."""
        if not colors:
            raise ValueError("Colors list cannot be empty")
        sanitized = [_sanitize_string(c) for c in colors]
        color_list = ", ".join(f'"{c}"' for c in sanitized)
        return fashion_lab_repository.find_all(
            filter_expr=f"base_colour in [{color_list}]", limit=limit,
        )

    def paginated_products(self, filter_expr: str, page: int, page_size: int) -> dict:
        """
        Pagination via the offset method.
        Equivalent to a QueryIterator; in production with millions of rows, 
        Collection.query_iterator() is preferred to avoid loading everything into memory.
        """
        if page < 1:
            raise ValueError("page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise ValueError("page_size must be between 1 and 100")
        offset = (page - 1) * page_size
        total = fashion_lab_repository.count(filter_expr)
        rows = fashion_lab_repository.find_all(
            filter_expr=filter_expr, limit=page_size, offset=offset,
        )
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size,
            "results": rows,
        }

    def advanced_filtered_search(
        self,
        query: str,
        genders: list[str] | None,
        seasons: list[str] | None,
        colours: list[str] | None,
        min_year: int | None,
        exclude_type: str | None,
        top_k: int,
    ) -> dict:
        """
        ANN Search with a complex boolean filter combining IN, AND, >=, and != operators.
        This uses pre-filtering (filtering is applied BEFORE the vector search).
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        parts = []
        if genders:
            g_list = ", ".join(f'"{_sanitize_string(g)}"' for g in genders)
            parts.append(f"gender in [{g_list}]")
        if seasons:
            s_list = ", ".join(f'"{_sanitize_string(s)}"' for s in seasons)
            parts.append(f"season in [{s_list}]")
        if colours:
            c_list = ", ".join(f'"{_sanitize_string(c)}"' for c in colours)
            parts.append(f"base_colour in [{c_list}]")
        if min_year is not None:
            parts.append(f"year >= {min_year}")
        if exclude_type:
            parts.append(f'article_type != "{_sanitize_string(exclude_type)}"')
        filter_expr = " && ".join(parts)
        qvec = embedding_service.encode_text_one(query)
        results = fashion_lab_repository.search(
            [qvec], "text_embedding", top_k=top_k, filter_expr=filter_expr,
        )[0]
        return {"filter_expr": filter_expr, "results": results}

    def search_by_threshold(self, query: str, min_score: float, top_k: int) -> list[dict]:
        """
        ANN Search with a post-filter score threshold.
        Retrieves top_k*10 candidates first, then discards those below the required score.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if not 0.0 <= min_score <= 1.0:
            raise ValueError("min_score must be between 0.0 and 1.0")
        qvec = embedding_service.encode_text_one(query)
        candidates = fashion_lab_repository.search(
            [qvec], "text_embedding", top_k=min(top_k * 10, 100),
        )[0]
        return [r for r in candidates if r.get("score", 0) >= min_score][:top_k]

    def count_by_category(self, category: str) -> dict:
        """COUNT(*) aggregation by master_category."""
        if not category:
            raise ValueError("Category cannot be empty")
        filter_expr = f'master_category == "{_sanitize_string(category)}"'
        count = fashion_lab_repository.count(filter_expr)
        return {"master_category": category, "count": count}

    def get_facets(self) -> dict:
        """
        Faceted search — counts occurrences of values for each categorical field.
        Useful for building UI filters (dropdown lists with item counts).
        """
        return fashion_lab_repository.get_facets(
            ["gender", "master_category", "base_colour", "season", "article_type"]
        )

    def get_random_sample(self, sample_size: int) -> list[dict]:
        """Returns a random sample from the collection for data exploration."""
        if sample_size < 1 or sample_size > 100:
            raise ValueError("sample_size must be between 1 and 100")
        return fashion_lab_repository.random_sample(sample_size)

    def create_products_batch(self, products: list) -> dict:
        """
        Batch insertion of multiple products.
        Encodes all names in a single model call (more efficient than individual calls).
        """
        if not products:
            raise ValueError("Product list cannot be empty")

        names = [p.product_name.strip()[:511] for p in products]
        if any(not n for n in names):
            raise ValueError("All products must have a non-empty product_name")

        text_embs = embedding_service.encode_text(names)
        zero = embedding_service.zero_vector()

        records = []
        for p, name, emb in zip(products, names, text_embs):
            records.append({
                "product_id":      0,
                "product_name":    name,
                "gender":          (p.gender or "")[:31],
                "master_category": (p.master_category or "")[:63],
                "sub_category":    (p.sub_category or "")[:63],
                "article_type":    (p.article_type or "")[:63],
                "base_colour":     (p.base_colour or "")[:63],
                "season":          (p.season or "")[:31],
                "year":            p.year or 0,
                "usage":           (p.usage or "")[:63],
                "has_image":       False,
                "text_embedding":  emb,
                "image_embedding": zero,
            })

        result = fashion_lab_repository.insert(records)
        return {
            "inserted_ids":  result.get("ids", []),
            "insert_count":  result.get("insert_count", 0),
        }

    def hybrid_text_search(self, query: str, top_k: int) -> list[dict]:
        """
        Hybrid search: encodes text and searches BOTH vector fields 
        (text_embedding + image_embedding) simultaneously using 
        Milvus AnnSearchRequest and RRF ranker.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        qvec = embedding_service.encode_text_one(query)
        return fashion_lab_repository.hybrid_search(qvec, top_k=top_k)

    def search_with_tuning(self, query: str, nprobe: int, top_k: int) -> list[dict]:
        """
        Search with an explicit nprobe parameter.
        Demonstrates how nprobe affects the accuracy and speed of the IVF_FLAT index.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if nprobe < 1:
            raise ValueError("nprobe must be >= 1")
        if top_k <= 0:
            raise ValueError("top_k must be positive")

        qvec = embedding_service.encode_text_one(query)
        return fashion_lab_repository.search_with_nprobe(
            [qvec], "text_embedding", top_k, nprobe,
        )[0]

    def get_stats(self) -> dict:
        """Vraća statistike kolekcije."""
        return fashion_lab_repository.get_stats()



fashion_lab_service = FashionLabService()