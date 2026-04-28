package models

// ─── Book ────────────────────────────────────────────────────────────────────
// Non-vectorised fields : isbn (VARCHAR), title (VARCHAR), author (VARCHAR)
// Vectorised field      : title_vector (FLOAT_VECTOR dim=768, COSINE AUTOINDEX)

type BookIn struct {
	ISBN   string `json:"isbn"   binding:"required"`
	Title  string `json:"title"  binding:"required"`
	Author string `json:"author" binding:"required"`
}

type BookUpdate struct {
	ISBN   *string `json:"isbn"`
	Title  *string `json:"title"`
	Author *string `json:"author"`
}

type BookOut struct {
	ID     int64   `json:"id"`
	ISBN   string  `json:"isbn"`
	Title  string  `json:"title"`
	Author string  `json:"author"`
	Score  float32 `json:"score,omitempty"`
}

// ─── Author ──────────────────────────────────────────────────────────────────
// Non-vectorised fields : name (VARCHAR), lastname (VARCHAR), author_id (VARCHAR)
// Vectorised field      : bio_vector (FLOAT_VECTOR dim=768, COSINE AUTOINDEX)

type AuthorIn struct {
	Name     string `json:"name"      binding:"required"`
	Lastname string `json:"lastname"  binding:"required"`
	AuthorID string `json:"author_id" binding:"required"`
	Country  string `json:"country"   binding:"required"`
}

type AuthorUpdate struct {
	Name     *string `json:"name"`
	Lastname *string `json:"lastname"`
	AuthorID *string `json:"author_id"`
	Country  *string `json:"country"`
}

type AuthorOut struct {
	ID       int64   `json:"id"`
	Name     string  `json:"name"`
	Lastname string  `json:"lastname"`
	AuthorID string  `json:"author_id"`
	Country  string  `json:"country"`
	Score    float32 `json:"score,omitempty"`
}
