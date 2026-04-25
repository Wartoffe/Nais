"""
Fashion Products — Milvus Report
====================================
Generates a comprehensive analytical report for the fashion_products collection:

  Section 1 — Collection Statistics (counts, distributions)
  Section 2 — Text Query Results (semantic search, filtered search)
  Section 3 — Image Query Results (URL-based, cross-modal text-to-image)
  Section 4 — Visualizations saved in report/output/
"""

import logging
import os
import sys
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")  
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import seaborn as sns
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymilvus import MilvusClient
from config import MILVUS_URI, FASHION_COLLECTION, NPROBE
from schema.milvus_schema import SCALAR_OUTPUT_FIELDS
from services.embedding_service import embedding_service

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Query examples used in Sections 2 and 3 ───────────────────────────────
SAMPLE_TEXT_QUERIES = [
    "blue denim jeans",
    "red summer dress for women",
    "white cotton casual shirt",
    "black leather formal shoes",
    "sports running sneakers",
]

SAMPLE_IMAGE_URL = (
    "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"
)  

TOP_K = 5
SEPARATOR = "=" * 72

def _save(fig: plt.Figure, name: str) -> str:
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    logger.info("Saved plot → %s", path)
    return path


def fetch_all(client: MilvusClient) -> list[dict]:
    """Fetches all records from the collection using offset pagination."""
    records: list[dict] = []
    batch_size = 1000
    offset = 0
    fields = [f for f in SCALAR_OUTPUT_FIELDS if f != "id"]

    while True:
        batch = client.query(
            collection_name=FASHION_COLLECTION,
            filter="",
            output_fields=fields,
            limit=batch_size,
            offset=offset,
        )
        if not batch:
            break
        records.extend(batch)
        if len(batch) < batch_size:
            break
        offset += batch_size
        logger.info("  fetched %d so far …", len(records))

    return records


def ann_search(client, query_vectors, anns_field, top_k=TOP_K):
    raw = client.search(
        collection_name=FASHION_COLLECTION,
        data=query_vectors,
        anns_field=anns_field,
        search_params={"metric_type": "COSINE", "params": {"nprobe": NPROBE}},
        limit=top_k,
        output_fields=["product_name", "gender", "article_type", "base_colour"],
    )
    results = []
    for hits in raw:
        batch = []
        for hit in hits:
            e = hit.get("entity", {})
            batch.append({
                "id":           hit["id"],
                "score":        round(hit["distance"], 4),
                "product_name": e.get("product_name", ""),
                "gender":       e.get("gender", ""),
                "article_type": e.get("article_type", ""),
                "base_colour":  e.get("base_colour", ""),
            })
        results.append(batch)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Section 1 — Collection Statistics
# ─────────────────────────────────────────────────────────────────────────────

def section1_stats(records: list[dict]) -> pd.DataFrame:
    print(f"\n{SEPARATOR}")
    print("SECTION 1 — COLLECTION STATISTICS")
    print(SEPARATOR)

    df = pd.DataFrame(records)
    total = len(df)
    has_image = df["has_image"].sum() if "has_image" in df.columns else "N/A"

    print(f"\nTotal products        : {total:,}")
    print(f"Products with image   : {has_image:,}")
    print(f"Products without image: {total - has_image:,}")

    for col in ("gender", "master_category", "season", "usage"):
        if col in df.columns:
            dist = df[col].value_counts()
            print(f"\nDistribution by {col}:")
            for val, cnt in dist.items():
                pct = cnt / total * 100
                print(f"  {val:<30} {cnt:>5}  ({pct:.1f}%)")

    year_col = df["year"] if "year" in df.columns else None
    if year_col is not None:
        valid_years = year_col[(year_col > 1900) & (year_col < 2030)]
        print(f"\nYear range: {int(valid_years.min())} – {int(valid_years.max())}")
        print(f"Most common year: {int(valid_years.mode()[0])}")

    print(f"\nTop 10 article types:")
    if "article_type" in df.columns:
        for val, cnt in df["article_type"].value_counts().head(10).items():
            print(f"  {val:<35} {cnt:>5}")

    print(f"\nTop 10 base colours:")
    if "base_colour" in df.columns:
        for val, cnt in df["base_colour"].value_counts().head(10).items():
            print(f"  {val:<35} {cnt:>5}")

    return df


# ─────────────────────────────────────────────────────────────────────────────
# Section 2 — Text Query Results
# ─────────────────────────────────────────────────────────────────────────────

def section2_text(client: MilvusClient) -> list[dict]:
    print(f"\n{SEPARATOR}")
    print("SECTION 2 — TEXT QUERY RESULTS")
    print(SEPARATOR)

    embeddings = embedding_service.encode_text(SAMPLE_TEXT_QUERIES)
    all_results = ann_search(client, embeddings, "text_embedding", top_k=TOP_K)

    aggregated = []  # for plotting in Section 4

    for query, hits in zip(SAMPLE_TEXT_QUERIES, all_results):
        print(f'\nQuery: "{query}"')
        print(f"  {'#':<3} {'Score':>6}  {'Product name':<45} {'Gender':<10} {'Type':<20}")
        print(f"  {'-'*3} {'-'*6}  {'-'*45} {'-'*10} {'-'*20}")
        for i, h in enumerate(hits, 1):
            print(
                f"  {i:<3} {h['score']:>6.4f}  "
                f"{h['product_name'][:44]:<45} "
                f"{h['gender'][:9]:<10} "
                f"{h['article_type'][:19]:<20}"
            )
        top_score = hits[0]["score"] if hits else 0.0
        aggregated.append({"query": query, "top_score": top_score, "hits": hits})

    # example of filtered search with a simple condition
    print(f'\n--- Filtered search: "casual shirt" filtered to gender=Men ---')
    flt_emb = embedding_service.encode_text_one("casual shirt")
    raw_flt = client.search(
        collection_name=FASHION_COLLECTION,
        data=[flt_emb],
        anns_field="text_embedding",
        search_params={"metric_type": "COSINE", "params": {"nprobe": NPROBE}},
        limit=TOP_K,
        filter='gender == "Men"',
        output_fields=["product_name", "article_type", "base_colour"],
    )
    for hits in raw_flt:
        for i, hit in enumerate(hits, 1):
            e = hit.get("entity", {})
            print(
                f"  {i}. [{hit['distance']:.4f}] "
                f"{e.get('product_name','')[:50]} | "
                f"{e.get('article_type','')} | "
                f"{e.get('base_colour','')}"
            )

    return aggregated


# ─────────────────────────────────────────────────────────────────────────────
# Section 3 — Image Query Results
# ─────────────────────────────────────────────────────────────────────────────

def section3_image(client: MilvusClient) -> dict:
    print(f"\n{SEPARATOR}")
    print("SECTION 3 — IMAGE QUERY RESULTS")
    print(SEPARATOR)

    print(f"\nImage URL: {SAMPLE_IMAGE_URL}")

    try:
        img = embedding_service.image_from_url(SAMPLE_IMAGE_URL)
        img_emb = embedding_service.encode_image_one(img)
    except Exception as exc:
        print(f"  [WARN] Could not fetch image: {exc}")
        return {}

    # Search: Image to image 
    print(f"\n--- Image → Image search (visual similarity) ---")
    img_results = ann_search(client, [img_emb], "image_embedding", top_k=TOP_K)
    for i, h in enumerate(img_results[0], 1):
        print(
            f"  {i}. [{h['score']:.4f}] "
            f"{h['product_name'][:50]} | "
            f"{h['gender']} | {h['base_colour']}"
        )

    # Cross-modal search: Text to Image
    print(f'\n--- Text → Image cross-modal search (query: "red sneakers") ---')
    txt_emb = embedding_service.encode_text_one("red sneakers")
    cross_results = ann_search(client, [txt_emb], "image_embedding", top_k=TOP_K)
    for i, h in enumerate(cross_results[0], 1):
        print(
            f"  {i}. [{h['score']:.4f}] "
            f"{h['product_name'][:50]} | "
            f"{h['gender']} | {h['base_colour']}"
        )

    # Cross-modal search: Image to Text
    print(f'\n--- Image → Text cross-modal search (image → product names) ---')
    imt_results = ann_search(client, [img_emb], "text_embedding", top_k=TOP_K)
    for i, h in enumerate(imt_results[0], 1):
        print(
            f"  {i}. [{h['score']:.4f}] "
            f"{h['product_name'][:50]} | "
            f"{h['gender']} | {h['article_type']}"
        )

    return {
        "img_emb":     img_emb,
        "img_results": img_results[0],
        "cross_results": cross_results[0],
        "imt_results":   imt_results[0],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Section 4 — Visualizations
# ─────────────────────────────────────────────────────────────────────────────

def plot_gender_bar(df: pd.DataFrame):
    counts = df["gender"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(counts.index, counts.values,
                  color=cm.tab10(np.linspace(0, 1, len(counts))))
    ax.bar_label(bars, padding=3)
    ax.set_title("Broj proizvoda po polu", fontsize=14, fontweight="bold")
    ax.set_xlabel("Pol")
    ax.set_ylabel("Broj")
    ax.set_ylim(0, counts.max() * 1.15)
    plt.tight_layout()
    return _save(fig, "01_gender_bar.png")


def plot_category_pie(df: pd.DataFrame):
    counts = df["master_category"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        counts.values,
        labels=counts.index,
        autopct="%1.1f%%",
        startangle=140,
        colors=cm.Set3(np.linspace(0, 1, len(counts))),
    )
    for t in autotexts:
        t.set_fontsize(9)
    ax.set_title("Distribucija po glavnoj kategoriji", fontsize=14, fontweight="bold")
    plt.tight_layout()
    return _save(fig, "02_category_pie.png")


def plot_article_type_hbar(df: pd.DataFrame):
    counts = df["article_type"].value_counts().head(15)
    fig, ax = plt.subplots(figsize=(10, 7))
    colors = cm.viridis(np.linspace(0.2, 0.8, len(counts)))
    bars = ax.barh(counts.index[::-1], counts.values[::-1], color=colors[::-1])
    ax.bar_label(bars, padding=3)
    ax.set_title("Top 15 tipova artikala", fontsize=14, fontweight="bold")
    ax.set_xlabel("Broj")
    plt.tight_layout()
    return _save(fig, "03_article_type_hbar.png")


def plot_colour_bar(df: pd.DataFrame):
    counts = df["base_colour"].value_counts().head(12)
    colours_map = {
        "Black": "#1a1a1a", "White": "#d0d0d0", "Blue": "#2196F3",
        "Red": "#F44336",   "Grey": "#9E9E9E",  "Navy Blue": "#1a237e",
        "Green": "#4CAF50", "Brown": "#795548",  "Pink": "#E91E63",
        "Yellow": "#FFEB3B","Purple": "#9C27B0", "Orange": "#FF9800",
    }
    bar_colors = [colours_map.get(c, "#aaaaaa") for c in counts.index]
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(counts.index, counts.values, color=bar_colors, edgecolor="white")
    ax.bar_label(bars, padding=3)
    ax.set_title("Top 12 osnovnih boja", fontsize=14, fontweight="bold")
    ax.set_xlabel("Boja")
    ax.set_ylabel("Broj")
    ax.set_xticklabels(counts.index, rotation=30, ha="right")
    ax.set_ylim(0, counts.max() * 1.15)
    plt.tight_layout()
    return _save(fig, "04_colour_bar.png")


def plot_year_histogram(df: pd.DataFrame):
    years = df["year"][(df["year"] > 1990) & (df["year"] < 2030)]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(years, bins=range(int(years.min()), int(years.max()) + 2),
            color="#42A5F5", edgecolor="white", rwidth=0.8)
    ax.set_title("Distribucija godina proizvoda", fontsize=14, fontweight="bold")
    ax.set_xlabel("Godina")
    ax.set_ylabel("Broj")
    ax.xaxis.set_tick_params(rotation=45)
    plt.tight_layout()
    return _save(fig, "05_year_histogram.png")


def plot_season_gender_heatmap(df: pd.DataFrame):
    pivot = df.groupby(["season", "gender"]).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(
        pivot, annot=True, fmt="d", cmap="YlOrRd",
        linewidths=0.5, linecolor="white", ax=ax,
    )
    ax.set_title("Broj proizvoda: Sezona × Pol", fontsize=14, fontweight="bold")
    ax.set_xlabel("Pol")
    ax.set_ylabel("Sezona")
    plt.tight_layout()
    return _save(fig, "06_season_gender_heatmap.png")


def plot_subcategory_stacked(df: pd.DataFrame):
    top_subcats = df["sub_category"].value_counts().head(8).index
    top_genders = df["gender"].value_counts().head(4).index
    sub_df = df[df["sub_category"].isin(top_subcats) & df["gender"].isin(top_genders)]
    pivot = sub_df.groupby(["sub_category", "gender"]).size().unstack(fill_value=0)
    pivot = pivot.loc[top_subcats]

    fig, ax = plt.subplots(figsize=(12, 6))
    pivot.plot(kind="bar", stacked=True, ax=ax,
               colormap="tab10", edgecolor="white", width=0.7)
    ax.set_title("Podkategorija × Pol (slagani grafik)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Podkategorija")
    ax.set_ylabel("Broj")
    ax.set_xticklabels(pivot.index, rotation=30, ha="right")
    ax.legend(title="Pol", bbox_to_anchor=(1.01, 1), loc="upper left")
    plt.tight_layout()
    return _save(fig, "07_subcategory_stacked.png")


def plot_text_search_scores(text_results: list[dict]):
    if not text_results:
        return
    fig, axes = plt.subplots(1, len(text_results), figsize=(16, 5), sharey=True)
    if len(text_results) == 1:
        axes = [axes]

    for ax, res in zip(axes, text_results):
        hits = res["hits"]
        labels = [f"#{i+1}" for i in range(len(hits))]
        scores = [h["score"] for h in hits]
        colors = cm.cool(np.linspace(0.3, 0.9, len(scores)))
        bars = ax.barh(labels[::-1], scores[::-1], color=colors[::-1])
        ax.bar_label(bars, fmt="%.3f", padding=3, fontsize=8)
        ax.set_title(res["query"][:28], fontsize=9, fontweight="bold")
        ax.set_xlim(0, 1.1)
        ax.set_xlabel("Kosinusna sličnost")

    fig.suptitle("Tekstualni upiti — Top-K kosinusne sličnosti",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    return _save(fig, "08_text_search_scores.png")


def plot_image_search_scores(img_data: dict):
    if not img_data or "img_results" not in img_data:
        return

    img_hits   = img_data["img_results"]
    cross_hits = img_data["cross_results"]
    imt_hits   = img_data["imt_results"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

    for ax, hits, title in zip(
        axes,
        [img_hits, cross_hits, imt_hits],
        ["Image → Image\n(vizuelna sličnost)",
         "Text → Image\n(\"red sneakers\")",
         "Image → Text\n(cross-modal)"],
    ):
        labels = [h["product_name"][:20] + "…" if len(h["product_name"]) > 20
                  else h["product_name"] for h in hits]
        scores = [h["score"] for h in hits]
        colors = cm.plasma(np.linspace(0.2, 0.8, len(scores)))
        ax.barh(range(len(labels))[::-1], scores, color=colors)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels[::-1], fontsize=8)
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.set_xlim(0, 1.1)
        ax.set_xlabel("Kosinusna sličnost")

    fig.suptitle("Rezultati upita po slici — sva tri modalitetna moda",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    return _save(fig, "09_image_search_scores.png")


def plot_score_rank_scatter(text_results: list[dict]):
    """Scatter dijagram: rang vs. ocena za sve tekstualne upite — prikazuje krivu pada."""
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = cm.tab10(np.linspace(0, 1, len(text_results)))
    for res, color in zip(text_results, colors):
        hits = res["hits"]
        ranks  = list(range(1, len(hits) + 1))
        scores = [h["score"] for h in hits]
        ax.plot(ranks, scores, marker="o", label=res["query"][:30], color=color)

    ax.set_title("Pad ocene po rangu (tekstualni upiti)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Pozicija ranga")
    ax.set_ylabel("Kosinusna sličnost")
    ax.set_xticks(range(1, TOP_K + 1))
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    return _save(fig, "10_score_rank_scatter.png")


def plot_usage_donut(df: pd.DataFrame):
    counts = df["usage"].value_counts()
    fig, ax = plt.subplots(figsize=(7, 7))
    wedge_props = {"width": 0.5, "edgecolor": "white"}
    wedges, texts, autotexts = ax.pie(
        counts.values,
        labels=counts.index,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops=wedge_props,
        colors=cm.Paired(np.linspace(0, 1, len(counts))),
    )
    for t in autotexts:
        t.set_fontsize(9)
    ax.set_title("Distribucija namene (prsten dijagram)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    return _save(fig, "11_usage_donut.png")


# ─────────────────────────────────────────────────────────────────────────────
# Main program
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(SEPARATOR)
    print("FASHION PRODUCTS — MILVUS REPORT")
    print(f"Collection : {FASHION_COLLECTION}")
    print(f"Milvus URI : {MILVUS_URI}")
    print(f"Output dir : {OUTPUT_DIR}")
    print(SEPARATOR)

    logger.info("Connecting to Milvus …")
    client = MilvusClient(uri=MILVUS_URI)

    # ── Section 1 ─────────────────────────────────────────────────────────────
    logger.info("Fetching all records …")
    records = fetch_all(client)
    print(f"\n[INFO] Total records fetched: {len(records)}")

    if not records:
        print("[ERROR] No records found — run ingestion first.")
        sys.exit(1)

    df = section1_stats(records)

    # ── Section 2 ─────────────────────────────────────────────────────────────
    text_results = section2_text(client)

    # ── Section 3 ─────────────────────────────────────────────────────────────
    img_data = section3_image(client)

    # ── Section 4 — Visualizations ─────────────────────────────────────────────
    print(f"\n{SEPARATOR}")
    print("SECTION 4 — GENERATING PLOTS")
    print(SEPARATOR)

    saved = []
    saved.append(plot_gender_bar(df))
    saved.append(plot_category_pie(df))
    saved.append(plot_article_type_hbar(df))
    saved.append(plot_colour_bar(df))
    saved.append(plot_year_histogram(df))
    saved.append(plot_season_gender_heatmap(df))
    saved.append(plot_subcategory_stacked(df))
    saved.append(plot_text_search_scores(text_results))
    saved.append(plot_image_search_scores(img_data))
    saved.append(plot_score_rank_scatter(text_results))
    saved.append(plot_usage_donut(df))

    print(f"\nAll plots saved to: {OUTPUT_DIR}")
    for p in saved:
        if p:
            print(f"  {os.path.basename(p)}")

    print(f"\n{SEPARATOR}")
    print("REPORT COMPLETE")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
