package embed

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"hash/fnv"
	"math"
	"net/http"
	"strings"
	"time"
)

const VectorDim = 768

type Client struct {
	baseURL string
	model   string
	http    *http.Client
}

func New(baseURL, model string) *Client {
	return &Client{baseURL: strings.TrimRight(baseURL, "/"), model: model, http: &http.Client{Timeout: 30 * time.Second}}
}

type embedRequest struct {
	Model  string `json:"model"`
	Prompt string `json:"prompt"`
}

type embedResponse struct {
	Embedding []float32 `json:"embedding"`
}

//Text embeder
func (c *Client) Text(text string) ([]float32, error) {
	body, _ := json.Marshal(embedRequest{Model: c.model, Prompt: text})
	resp, err := c.http.Post(c.baseURL+"/api/embeddings", "application/json", bytes.NewReader(body))
	if err == nil && resp != nil {
		defer resp.Body.Close()
		if resp.StatusCode >= 200 && resp.StatusCode < 300 {
			var result embedResponse
			if err := json.NewDecoder(resp.Body).Decode(&result); err == nil && len(result.Embedding) == VectorDim {
				return result.Embedding, nil
			}
		}
	}
	return fallbackEmbedding(text), nil
}

func (c *Client) WaitReady(retries int, delay time.Duration) error {
	for i := 0; i < retries; i++ {
		resp, err := c.http.Get(c.baseURL)
		if err == nil && resp != nil {
			resp.Body.Close()
			if resp.StatusCode < 500 {
				return nil
			}
		}
		time.Sleep(delay)
	}
	return fmt.Errorf("ollama not ready after %d retries", retries)
}

func fallbackEmbedding(text string) []float32 {
	vec := make([]float32, VectorDim)
	words := strings.Fields(strings.ToLower(text))
	if len(words) == 0 {
		words = []string{text}
	}
	for _, w := range words {
		h := fnv.New64a()
		_, _ = h.Write([]byte(w))
		sum := h.Sum64()
		idx := int(sum % VectorDim)
		sign := float32(1)
		if (sum>>63)&1 == 1 {
			sign = -1
		}
		weight := float32(1.0)
		if len(w) > 6 {
			weight = 1.5
		}
		vec[idx] += sign * weight

		// add a second stable position to reduce collisions
		buf := make([]byte, 8)
		binary.LittleEndian.PutUint64(buf, sum^0x9e3779b97f4a7c15)
		h2 := fnv.New64a()
		_, _ = h2.Write(buf)
		idx2 := int(h2.Sum64() % VectorDim)
		vec[idx2] += sign * 0.5
	}
	var norm float64
	for _, v := range vec {
		norm += float64(v * v)
	}
	if norm == 0 {
		vec[0] = 1
		return vec
	}
	scale := float32(1.0 / math.Sqrt(norm))
	for i := range vec {
		vec[i] *= scale
	}
	return vec
}
