# search-service

Go microservice for KT1: Milvus vector database with one logical cluster (`library_cluster`) and two collections (`books`, `authors`).

## Pokretanje

```bash
docker compose up --build
```

Servis je dostupan na `http://localhost:8080`.

Ollama je opciona za kvalitetnije embeddings. Ako zelite realan model umesto fallback embeddings:

```bash
docker compose exec ollama ollama pull nomic-embed-text
docker compose restart search-service
```

## Kolekcije

- `books`: `isbn`, `title`, `author`, `title_vector`
- `authors`: `name`, `lastname`, `author_id`, `bio_vector`

Na startup-u se kreiraju kolekcije, formiraju AUTOINDEX/COSINE indeksi nad vektorskim poljima i ubacuje se najmanje 200 slogova po kolekciji.

## Primeri ruta

CRUD:

- `GET /books?limit=20`
- `GET /books/search?query=dystopian novel&top_k=5`
- `POST /books`
- `PUT /books/:id`
- `DELETE /books/:id`
- `GET /authors?limit=20`
- `GET /authors/search?query=orwell&top_k=5`

Prosti/slozeni upiti:

- `GET /queries/books/count-by-author?author=George Orwell`
- `GET /queries/authors/by-author-id?author_id=AUTH002`
- `GET /queries/books/search-filtered?query=dystopian&author=George Orwell&isbn=978-0-7432-7356-5&top_k=5`
- `GET /queries/authors/search-filtered?query=orwell&lastname=Orwell&author_id=AUTH002&top_k=5`
- `GET /queries/books/hybrid?query=animal&text=farm&top_k=10`
