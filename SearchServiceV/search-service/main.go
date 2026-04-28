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

	milvusAddr := fmt.Sprintf("%s:%s", cfg.MilvusHost, cfg.MilvusPort)
	milvusClient, err := client.NewGrpcClient(context.Background(), milvusAddr)
	if err != nil {
		log.Fatalf("failed to connect to Milvus at %s: %v", milvusAddr, err)
	}
	defer milvusClient.Close()

	// ── Ensure library_cluster database exists and switch to it ──────────────
	dbs, err := milvusClient.ListDatabases(context.Background())
	if err != nil {
		log.Fatalf("failed to list Milvus databases: %v", err)
	}
	found := false
	for _, db := range dbs {
		if db.Name == schema.ClusterDBName {
			found = true
			break
		}
	}
	if !found {
		if err := milvusClient.CreateDatabase(context.Background(), schema.ClusterDBName); err != nil {
			log.Fatalf("failed to create database %s: %v", schema.ClusterDBName, err)
		}
		log.Printf("created Milvus database: %s", schema.ClusterDBName)
	}
	if err := milvusClient.UsingDatabase(context.Background(), schema.ClusterDBName); err != nil {
		log.Fatalf("failed to switch to database %s: %v", schema.ClusterDBName, err)
	}
	log.Printf("using Milvus database: %s", schema.ClusterDBName)
	// ─────────────────────────────────────────────────────────────────────────

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
		authors.GET("/:id", authorHandler.Get)
		authors.PUT("/:id", authorHandler.Update)
		authors.DELETE("/:id", authorHandler.Delete)
	}

	queries := r.Group("/queries")
	{
		queries.GET("/books/hybrid", bookHandler.HybridSearch)
		queries.GET("/books/search-iterator", bookHandler.SearchWithIterator)
		queries.GET("/authors/search-iterator", authorHandler.SearchWithIterator)
	}

	log.Printf("search-service listening on :%s", cfg.ServerPort)
	if err := r.Run(":" + cfg.ServerPort); err != nil {
		log.Fatal(err)
	}
}
