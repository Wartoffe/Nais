import csv
import json
import urllib.request
import re

ES_URL = "http://elasticsearchbooks:9200"

BOOKS_INDEX = "books"
REVIEWS_INDEX = "reviews"

#
# MAPPING ZA BOOKS NA OSNOVU BOOK MODELA
#

BOOKS_MAPPING = {
    "mappings": {
        "properties": {
            "bookId":           {"type": "keyword"},
            "title":            {"type": "text", "analyzer": "standard"},
            "series":           {"type": "text", "analyzer": "standard"},
            "author":           {"type": "keyword"},
            "rating":           {"type": "double"},
            "description":      {"type": "text", "analyzer": "standard"},
            "language":         {"type": "keyword"},
            "isbn":             {"type": "keyword"},
            "genres":           {"type": "keyword"},
            "characters":       {"type": "keyword"},
            "bookForm":         {"type": "keyword"},
            "edition":          {"type": "keyword"},
            "pages":            {"type": "integer"},
            "publisher":        {"type": "keyword"},
            "publishDate": {
                "type":   "date",
                "format": "M/d/yyyy"
            },
            "firstPublishDate": {
                "type":   "date",
                "format": "M/d/yyyy"
            },
            "awards":           {"type": "keyword"},
            "numRatings":       {"type": "integer"},
            "ratingsByStars":   {"type": "integer"},
            "likedPercent":     {"type": "double"},
            "setting":          {"type": "keyword"},
            "coverImg":         {"type": "keyword"},
            "bbeScore":         {"type": "double"},
            "bbeVotes":         {"type": "integer"},
            "price":            {"type": "double"}
        }
    }
}

#
# MAPPING ZA REVIEWS NA OSNOVU REVIEW MODELA
#

REVIEWS_MAPPING = {
    "mappings": {
        "properties": {
            "reviewId":     {"type": "keyword"},
            "userId":       {"type": "keyword"},
            "bookId":       {"type": "keyword"},
            "rating":       {"type": "integer"},
            "reviewText":   {"type": "text", "analyzer": "standard"},
            "dateAdded": {
                "type":   "date",
                "format": "EEE MMM d HH:mm:ss Z yyyy"
            },
            "dateUpdated": {
                "type":   "date",
                "format": "EEE MMM d HH:mm:ss Z yyyy"
            },
            "readAt": {
                "type":   "date",
                "format": "EEE MMM d HH:mm:ss Z yyyy"
            },
            "startedAt": {
                "type":   "date",
                "format": "EEE MMM d HH:mm:ss Z yyyy"
            },
            "nVotes":       {"type": "integer"},
            "nComments":    {"type": "integer"}
        }
    }
}

#
# POMOCNE FUNKCIJE
#

def safe_int(val):
    try:
        return int(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def safe_float(val):
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def parse_list_field(val, item_type=str):
    if not val or val.strip() == "":
        return []
    val = val.strip()
    if val.startswith("["):
        if item_type == str:
            items = re.findall(r"'([^']*)'", val)
            return items if items else []
        else:
            items = re.findall(r"[\d.]+", val)
            return [item_type(i) for i in items] if items else []
    try:
        return [item_type(val)]
    except (ValueError, TypeError):
        return [val]


def create_index(index_name, mapping):
    """Kreira indeks sa datim mappingom. Ako već postoji, preskače."""
    url = f"{ES_URL}/{index_name}"
    try:
        check_req = urllib.request.Request(url, method="HEAD")
        urllib.request.urlopen(check_req)
        print(f"Indeks '{index_name}' već postoji, preskačem kreiranje.")
        return
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise

    data = json.dumps(mapping).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="PUT"
    )
    with urllib.request.urlopen(req) as resp:
        print(f"Indeks '{index_name}' kreiran: {resp.read().decode()}")


def send_bulk(lines):
    body = "\n".join(lines) + "\n"
    data = body.encode("utf-8")
    req = urllib.request.Request(
        f"{ES_URL}/_bulk",
        data=data,
        headers={"Content-Type": "application/x-ndjson"}
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        if result.get("errors"):
            for item in result["items"]:
                if "error" in item.get("index", {}):
                    print(f"  ERROR: {item['index']['error']}")
                    break


def is_index_empty(index_name):
    url = f"{ES_URL}/{index_name}/_count"
    try:
        with urllib.request.urlopen(url) as resp:
            result = json.loads(resp.read())
            return result.get("count", 0) == 0
    except:
        return True

#
# UCITAVANJE KNJIGA
#

def load_books(csv_path, batch_size=500, limit=10000):
    print(f"\nUčitavam books iz: {csv_path} (max {limit})")
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        batch = []
        total = 0

        for count, row in enumerate(reader):
            if count >= limit:
                break

            book_id = row.get("bookId", "").strip()
            if not book_id:
                continue

            meta = json.dumps({"index": {"_index": BOOKS_INDEX, "_id": book_id}})
            doc = json.dumps({
                "bookId":           book_id,
                "title":            row.get("title", "").strip() or None,
                "series":           row.get("series", "").strip() or None,
                "author":           row.get("author", "").strip() or None,
                "rating":           safe_float(row.get("rating")),
                "description":      row.get("description", "").strip() or None,
                "language":         row.get("language", "").strip() or None,
                "isbn":             row.get("isbn", "").strip() or None,
                "genres":           parse_list_field(row.get("genres", "")),
                "characters":       parse_list_field(row.get("characters", "")),
                "bookForm":         row.get("bookForm", "").strip() or None,
                "edition":          row.get("edition", "").strip() or None,
                "pages":            safe_int(row.get("pages")),
                "publisher":        row.get("publisher", "").strip() or None,
                "publishDate":      row.get("publishDate", "").strip() or None,
                "firstPublishDate": row.get("firstPublishDate", "").strip() or None,
                "awards":           parse_list_field(row.get("awards", "")),
                "numRatings":       safe_int(row.get("numRatings")),
                "ratingsByStars":   parse_list_field(row.get("ratingsByStars", ""), item_type=int),
                "likedPercent":     safe_float(row.get("likedPercent")),
                "setting":          parse_list_field(row.get("setting", "")),
                "coverImg":         row.get("coverImg", "").strip() or None,
                "bbeScore":         safe_float(row.get("bbeScore")),
                "bbeVotes":         safe_int(row.get("bbeVotes")),
                "price":            safe_float(row.get("price"))
            })

            batch.append(meta)
            batch.append(doc)

            if len(batch) >= batch_size * 2:
                send_bulk(batch)
                total += len(batch) // 2
                print(f"  Indeksirano {total} knjiga...")
                batch = []

        if batch:
            send_bulk(batch)
            total += len(batch) // 2
            print(f"  Ukupno indeksirano {total} knjiga.")

#
# UCITAVANJE RECENZIJA
#

def load_reviews(json_path, batch_size=500, limit=10000):
    print(f"\nUčitavam reviews iz: {json_path} (max {limit})")
    with open(json_path, encoding="utf-8-sig") as f:
        batch = []
        total = 0
 
        for count, line in enumerate(f):
            if count >= limit:
                break
 
            line = line.strip()
            if not line:
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                print(f" UPOZORENJE: neispravan JSON na redu {count + 1}, preskačem.")
                continue

            review_id = row.get("review_id", "")
            if not review_id:
                continue
 
            meta = json.dumps({"index": {"_index": REVIEWS_INDEX, "_id": review_id}})
            doc  = json.dumps({
                "reviewId":    review_id,
                "userId":      row.get("user_id")    or None,
                "bookId":      row.get("book_id")    or None,
                "rating":      safe_int(row.get("rating")),
                "reviewText":  row.get("review_text") or None,
                "dateAdded":   row.get("date_added")   or None,
                "dateUpdated": row.get("date_updated") or None,
                "readAt":      row.get("read_at")    or None,
                "startedAt":   row.get("started_at") or None,
                "nVotes":      safe_int(row.get("n_votes")),
                "nComments":   safe_int(row.get("n_comments")),
            })
 
            batch.append(meta)
            batch.append(doc)
 
            if len(batch) >= batch_size * 2:
                send_bulk(batch)
                total += len(batch) // 2
                print(f"  Indeksirano {total} recenzija...")
                batch = []
 
        if batch:
            send_bulk(batch)
            total += len(batch) // 2
            print(f"  Ukupno indeksirano {total} recenzija.")


if __name__ == "__main__":
    # 1. Unos knjiga
    print("--- [1/2] Unos knjiga ---")
    if is_index_empty(BOOKS_INDEX):
        create_index(BOOKS_INDEX, BOOKS_MAPPING)
        load_books("books.csv")
    print("--- [1/2] Unos knjiga gotov! ---")

    # 2. Unos recenzija
    print("--- [2/2] Unos recenzija ---")
    if is_index_empty(REVIEWS_INDEX):
        create_index(REVIEWS_INDEX, REVIEWS_MAPPING)
        load_reviews("reviews.json")
    print("--- [2/2] Unos recenzija gotov! ---")

    print("Gotovo!")
