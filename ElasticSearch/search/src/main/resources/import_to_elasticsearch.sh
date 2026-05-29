#!/bin/bash
ES_HOST="${1:-http://localhost:9200}"

echo "==> Creating index: books_text"
curl -s -X PUT "$ES_HOST/books_text" \
  -H 'Content-Type: application/json' \
  -d @books_text_mapping.json | python3 -m json.tool

echo ""
echo "==> Creating index: books_keyword"
curl -s -X PUT "$ES_HOST/books_keyword" \
  -H 'Content-Type: application/json' \
  -d @books_keyword_mapping.json | python3 -m json.tool

echo ""
echo "==> Bulk importing books_text (1000 records)..."
curl -s -X POST "$ES_HOST/_bulk" \
  -H 'Content-Type: application/x-ndjson' \
  --data-binary @books_text_bulk.ndjson | python3 -c "
import sys,json; d=json.load(sys.stdin)
errs=[i for i in d.get('items',[]) if list(i.values())[0].get('status',200)>=400]
print(f'books_text:    {len(d["items"])} items, {len(errs)} errors')
"

echo ""
echo "==> Bulk importing books_keyword (1000 records)..."
curl -s -X POST "$ES_HOST/_bulk" \
  -H 'Content-Type: application/x-ndjson' \
  --data-binary @books_keyword_bulk.ndjson | python3 -c "
import sys,json; d=json.load(sys.stdin)
errs=[i for i in d.get('items',[]) if list(i.values())[0].get('status',200)>=400]
print(f'books_keyword: {len(d["items"])} items, {len(errs)} errors')
"

echo ""
echo "==> Counts:"
curl -s "$ES_HOST/books_text/_count"    | python3 -m json.tool
curl -s "$ES_HOST/books_keyword/_count" | python3 -m json.tool
