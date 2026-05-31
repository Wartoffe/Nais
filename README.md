# Nais

Komanda za pokretanje potrebnih stvari za Nenadov deo za KT2 je:
```
docker-compose up -d etcd minio standalone ollama redis-cache-books eureka-server vector-database-service streamlit attu elasticsearchbooks elasticsearchbooks-init kibanabooks elastic-search-books-reviews-service --build
```

Komanda za pokretanje potrebnih stvari za Marijin deo za KT2 je:
```
docker-compose up -d eureka-server influxdb timeseries-service timeseries-redis --build
```