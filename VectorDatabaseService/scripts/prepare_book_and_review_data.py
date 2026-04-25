"""
Skripta koja se jednom pokreće kako bi se spremili skupovi podataka u lokalne Parquet fajlove.
Zadatak same skripte jeste da učita informacije o 1000 knjiga, kao i 5 recenzija za svaku od knjiga.

Skup podataka za knjige: https://zenodo.org/records/4265096
Skup podataka za recenzije: https://cseweb.ucsd.edu/~jmcauley/datasets/goodreads.html
"""


import pandas as pd
import gzip, json
import requests
from PIL import Image
from io import BytesIO
from tqdm import tqdm

BOOKS_TARGET  = 1000
REVIEWS_PER_BOOK = 5
REVIEWS_TARGET = BOOKS_TARGET * REVIEWS_PER_BOOK


def fetch_image_bytes(url: str) -> bytes | None:
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        Image.open(BytesIO(resp.content)).verify()
        return resp.content
    except Exception:
        return None


def fetch_images_with_progress(df: pd.DataFrame) -> pd.Series:
    """Preuzima slike za sve knjige uz progress bar."""
    results = []
    # tqdm omota iterrows() — svaki red je jedna knjiga
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Preuzimanje slika", unit="knjiga"):
        results.append(fetch_image_bytes(row["coverImg"]))
        # Checkpoint svake 100 knjige
        done = len(results)
        if done % 100 == 0:
            ok  = sum(1 for r in results if r is not None)
            fail = done - ok
            tqdm.write(f"  ✔ {done}/{len(df)} | uspešno: {ok} | neuspešno: {fail}")
    return pd.Series(results, index=df.index)


# ── 1. Učitaj Zenodo dataset ─────────────────────────────────────────────────
print("\n[1/4] Učitavanje Zenodo dataseta...")
books_df = pd.read_csv("Books.csv")
print(f"      Ukupno redova u CSV-u: {len(books_df):,}")

books_sample = (
    books_df
    .dropna(subset=["isbn", "description", "coverImg"])
    .head(BOOKS_TARGET)
)
print(f"      Nakon filtriranja (isbn+description+coverImg): {len(books_sample):,} knjiga")

books_sample = books_sample.copy()
books_sample["goodreads_id"] = (
    books_sample["bookId"].str.extract(r"^(\d+)", expand=False)
)
valid_ids = set(books_sample["goodreads_id"].astype(str))

# ── 2. Preuzimanje slika ──────────────────────────────────────────────────────
print(f"\n[2/4] Preuzimanje naslovnih slika za {len(books_sample)} knjiga...")
books_sample["image_bytes"] = fetch_images_with_progress(books_sample)
books_sample["has_image"]   = books_sample["image_bytes"].notna()

ok_count = books_sample["has_image"].sum()
print(f"      Završeno — slike preuzete: {ok_count}/{len(books_sample)}")

# ── 3. Učitaj UCSD reviews (stream) ──────────────────────────────────────────
print(f"\n[3/4] Streaming čitanje recenzija (cilj: {REVIEWS_TARGET})...")

reviews        = []
lines_read     = 0
reviews_by_book: dict[str, int] = {}   # book_id → broj već skupljenih recenzija

with gzip.open("goodreads_reviews_dedup.json.gz", "rt") as f:
    # tqdm bez poznatog totala — prati broj pročitanih linija
    pbar = tqdm(f, desc="Čitanje linija", unit=" linija", miniters=100_000)
    for line in pbar:
        lines_read += 1
        r = json.loads(line)
        bid = str(r["book_id"])

        if bid in valid_ids and r.get("review_text", "").strip():
            # Uzmi max 5 recenzija po knjizi već ovde (efikasnije)
            if reviews_by_book.get(bid, 0) < REVIEWS_PER_BOOK:
                reviews.append(r)
                reviews_by_book[bid] = reviews_by_book.get(bid, 0) + 1

                # Checkpoint svake 100 nađenih recenzija
                if len(reviews) % 100 == 0:
                    books_covered = len(reviews_by_book)
                    tqdm.write(
                        f"  ✔ recenzija: {len(reviews)}/{REVIEWS_TARGET}"
                        f" | knjiga pokriveno: {books_covered}/{BOOKS_TARGET}"
                        f" | linija pročitano: {lines_read:,}"
                    )

        # Prekini čim sakupimo sve recenzije
        if len(reviews) >= REVIEWS_TARGET:
            break

    pbar.close()

print(f"      Završeno — recenzija: {len(reviews)} | linija pročitano: {lines_read:,}")

# ── 4. Join i snimanje ────────────────────────────────────────────────────────
print("\n[4/4] Join, finalizacija i snimanje Parquet fajlova...")

reviews_df         = pd.DataFrame(reviews)
isbn_map           = books_sample.set_index("goodreads_id")["isbn"].to_dict()
reviews_df["isbn"] = reviews_df["book_id"].astype(str).map(isbn_map)
reviews_df         = reviews_df.dropna(subset=["isbn"])

reviews_final = (
    reviews_df
    .groupby("isbn")
    .head(REVIEWS_PER_BOOK)
    .reset_index(drop=True)
)

books_final = books_sample[[
    "goodreads_id", "isbn", "title", "author",
    "description", "language",
    "coverImg", "publisher", "pages",
    "image_bytes", "has_image",
]]

reviews_final = reviews_final[[
    "review_id", "isbn", "book_id",
    "review_text", "rating", "date_added", "n_votes",
]]

books_final.to_parquet("../data/books.parquet", index=False)
reviews_final.to_parquet("../data/book_reviews.parquet", index=False)

# ── Finalni izveštaj ──────────────────────────────────────────────────────────
print("\n" + "─" * 50)
print("ZAVRŠENO")
print("─" * 50)
print(f"  Knjige snimljene:    {len(books_final):>6,}  →  ../data/books.parquet")
print(f"  Recenzije snimljene: {len(reviews_final):>6,}  →  ../data/book_reviews.parquet")
print(f"  Knjiga sa slikom:    {books_final['has_image'].sum():>6,} / {len(books_final)}")
print(f"  Knjiga sa recenzijom:{reviews_final['isbn'].nunique():>6,} / {len(books_final)}")
print("─" * 50)