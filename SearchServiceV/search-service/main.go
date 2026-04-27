package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/milvus-io/milvus-sdk-go/v2/client"

	"search-service/config"
	"search-service/embed"
	"search-service/handlers"
	"search-service/schema"
	"search-service/seed"
)

func main() {
	cfg := config.Load()
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()

	milvusAddr := fmt.Sprintf("%s:%s", cfg.MilvusHost, cfg.MilvusPort)
	milvusClient, err := client.NewGrpcClient(ctx, milvusAddr)
	if err != nil {
		log.Fatalf("failed to connect to Milvus at %s: %v", milvusAddr, err)
	}
	defer milvusClient.Close()

	embedder := embed.New(cfg.OllamaURL, cfg.OllamaModel)
	if err := embedder.WaitReady(5, 2*time.Second); err != nil {
		log.Printf("warning: %v; using local deterministic fallback embeddings until Ollama is available", err)
	}

	if err := schema.EnsureCollections(context.Background(), milvusClient); err != nil {
		log.Fatalf("failed to ensure Milvus collections: %v", err)
	}

	if err := seed.SeedIfEmpty(context.Background(), milvusClient, embedder); err != nil {
		log.Fatalf("failed to seed Milvus data: %v", err)
	}

	r := gin.Default()
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok", "cluster": schema.ClusterDBName})
	})

	bookHandler := handlers.NewBookHandler(milvusClient, embedder)
	authorHandler := handlers.NewAuthorHandler(milvusClient, embedder)

	books := r.Group("/books")
	{
		books.POST("", bookHandler.Create)
		books.GET("", bookHandler.List)
		books.GET("/search", bookHandler.Search)
		books.GET("/:id", bookHandler.Get)
		books.PUT("/:id", bookHandler.Update)
		books.DELETE("/:id", bookHandler.Delete)
	}

	authors := r.Group("/authors")
	{
		authors.POST("", authorHandler.Create)
		authors.GET("", authorHandler.List)
		authors.GET("/search", authorHandler.Search)
		authors.GET("/:id", authorHandler.Get)
		authors.PUT("/:id", authorHandler.Update)
		authors.DELETE("/:id", authorHandler.Delete)
	}

	queries := r.Group("/queries")
	{
		queries.GET("/books/count-by-author", bookHandler.CountByAuthor)
		queries.GET("/books/search-filtered", bookHandler.SearchFiltered)
		queries.GET("/books/hybrid", bookHandler.HybridSearch)
		queries.GET("/authors/by-author-id", authorHandler.ByAuthorID)
		queries.GET("/authors/search-filtered", authorHandler.SearchFiltered)
	}

	log.Printf("search-service listening on :%s", cfg.ServerPort)
	if err := r.Run(":" + cfg.ServerPort); err != nil {
		log.Fatal(err)
	}
}
