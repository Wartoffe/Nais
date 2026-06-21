#!/bin/bash
# Seeds 10 books into ColumnarDBService that share their ISBN with a real
# document already indexed in Elasticsearch (books_bulk.ndjson), so the
# saga's ISBN-based hide/unhide has something real to match against.
#
# Run against the already-running stack: no restart/rebuild needed.

BASE_URL="http://localhost:9060/books"

post() {
  curl -s -X POST "$BASE_URL" -H "Content-Type: application/json" -d "$1"
  echo ""
}

# Normal stock (2-4 available) -- general borrow/return testing, won't hit zero on one loan
post '{"bookId":"20000000-0000-0000-0000-000000000009","genre":"ES Import","title":"Silver Tongue","author":"Sarah Yamamoto","isbn":"9790855026256","publishedYear":1969,"totalCopies":4,"availableCopies":3}'
post '{"bookId":"20000000-0000-0000-0000-000000000010","genre":"ES Import","title":"The Mirror","author":"Olivia Kato","isbn":"9794617327438","publishedYear":1954,"totalCopies":4,"availableCopies":3}'
post '{"bookId":"20000000-0000-0000-0000-000000000011","genre":"ES Import","title":"A Promise","author":"Wei Yang","isbn":"9796775138772","publishedYear":1970,"totalCopies":5,"availableCopies":4}'
post '{"bookId":"20000000-0000-0000-0000-000000000014","genre":"ES Import","title":"Lost Horizon","author":"Olivia Sánchez","isbn":"9786669874220","publishedYear":1984,"totalCopies":4,"availableCopies":2}'
post '{"bookId":"20000000-0000-0000-0000-000000000015","genre":"ES Import","title":"Cold Light","author":"Stefan Garcia","isbn":"9797441662140","publishedYear":1999,"totalCopies":4,"availableCopies":2}'
post '{"bookId":"20000000-0000-0000-0000-000000000016","genre":"ES Import","title":"The Rising Tide","author":"Oliver Wagner","isbn":"9783154230608","publishedYear":1975,"totalCopies":4,"availableCopies":2}'
post '{"bookId":"20000000-0000-0000-0000-000000000017","genre":"ES Import","title":"The Forgotten King","author":"Steven Moore","isbn":"9783480424795","publishedYear":1952,"totalCopies":4,"availableCopies":2}'

# Low stock (availableCopies = 1) -- ONE createLoan call on any of these
# drops it to 0 and fires HIDE_REQUESTED immediately
post '{"bookId":"20000000-0000-0000-0000-000000000012","genre":"ES Import","title":"The Hidden Path","author":"Lucas Becker","isbn":"9794566983983","publishedYear":1974,"totalCopies":3,"availableCopies":1}'
post '{"bookId":"20000000-0000-0000-0000-000000000013","genre":"ES Import","title":"The Lost City","author":"Sakura Volkov","isbn":"9792695753859","publishedYear":1964,"totalCopies":3,"availableCopies":1}'
post '{"bookId":"20000000-0000-0000-0000-000000000018","genre":"ES Import","title":"The Storm","author":"William González","isbn":"9797027303825","publishedYear":2002,"totalCopies":3,"availableCopies":1}'

echo "Done. Verify with: curl 'http://localhost:9060/books?genre=ES%20Import'"
