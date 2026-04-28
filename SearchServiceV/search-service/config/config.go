package config

import "os"

type Config struct {
	MilvusHost  string
	MilvusPort  string
	OllamaURL   string
	OllamaModel string
	ServerPort  string
}

func Load() *Config {
	return &Config{
		MilvusHost:  getEnv("MILVUS_HOST", "localhost"),
		MilvusPort:  getEnv("MILVUS_PORT", "19530"),
		OllamaURL:   getEnv("OLLAMA_URL", "http://localhost:11434"),
		OllamaModel: getEnv("OLLAMA_MODEL", "nomic-embed-text"),
		ServerPort:  getEnv("SERVER_PORT", "8080"),
	}
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}
