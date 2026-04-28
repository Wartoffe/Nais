package handlers

import (
	"context"
	"fmt"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/milvus-io/milvus-sdk-go/v2/client"
	"github.com/milvus-io/milvus-sdk-go/v2/entity"
	"google.golang.org/grpc/metadata"

	"search-service/embed"
	"search-service/models"
	"search-service/schema"
)

type BookHandler struct {
	milvus   client.Client
	embedder *embed.Client
}

func NewBookHandler(milvus client.Client, embedder *embed.Client) *BookHandler {
	return &BookHandler{milvus: milvus, embedder: embedder}
}

func safeCtx(c *gin.Context) context.Context {
	ctx := c.Request.Context()
	if ctx == nil {
		ctx = context.Background()
	}
	return ctx
}

func checkClient(c *gin.Context, milvus client.Client) bool {
	if milvus == nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "milvus client not initialized"})
		return false
	}
	return true
}

// POST /books
func (h *BookHandler) Create(c *gin.Context) {
	if !checkClient(c, h.milvus) {
		return
	}

	var in models.BookIn
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	vec, err := h.embedder.Text(in.Title + " " + in.Author)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "embedding failed: " + err.Error()})
		return
	}

	isbn := []string{in.ISBN}
	title := []string{in.Title}
	author := []string{in.Author}
	vectors := [][]float32{vec}

	ctx := safeCtx(c)
	result, err := h.milvus.Insert(ctx, schema.CollectionBooks, "",
		entity.NewColumnVarChar("isbn", isbn),
		entity.NewColumnVarChar("title", title),
		entity.NewColumnVarChar("author", author),
		entity.NewColumnFloatVector("title_vector", schema.VectorDim, vectors),
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, gin.H{"inserted_id": result.(*entity.ColumnInt64).Data()[0]})
}

// GET /books
func (h *BookHandler) List(c *gin.Context) {
	if !checkClient(c, h.milvus) {
		return
	}

	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))

	outputFields := []string{"id", "isbn", "title", "author"}
	ctx := safeCtx(c)
	results, err := h.milvus.Query(ctx, schema.CollectionBooks, nil,
		"id > 0", outputFields,
		client.WithLimit(int64(limit)),
		client.WithOffset(int64(offset)),
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	books := colsToBooks(results)
	c.JSON(http.StatusOK, books)
}

// GET /books/:id
func (h *BookHandler) Get(c *gin.Context) {
	if !checkClient(c, h.milvus) {
		return
	}

	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}

	ctx := safeCtx(c)
	results, err := h.milvus.QueryByPks(ctx, schema.CollectionBooks, nil,
		entity.NewColumnInt64("id", []int64{id}),
		[]string{"id", "isbn", "title", "author"},
	)
	if err != nil || len(results) == 0 || results[0].Len() == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("book %d not found", id)})
		return
	}

	books := colsToBooks(results)
	c.JSON(http.StatusOK, books[0])
}

// PUT /books/:id
func (h *BookHandler) Update(c *gin.Context) {
	if !checkClient(c, h.milvus) {
		return
	}

	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}

	var upd models.BookUpdate
	if err := c.ShouldBindJSON(&upd); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	ctx := safeCtx(c)
	// fetch existing
	existing, err := h.milvus.QueryByPks(ctx, schema.CollectionBooks, nil,
		entity.NewColumnInt64("id", []int64{id}),
		[]string{"id", "isbn", "title", "author"},
	)
	if err != nil || len(existing) == 0 || existing[0].Len() == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("book %d not found", id)})
		return
	}

	current := colsToBooks(existing)[0]
	newISBN := current.ISBN
	newTitle := current.Title
	newAuthor := current.Author
	if upd.ISBN != nil {
		newISBN = *upd.ISBN
	}
	if upd.Title != nil {
		newTitle = *upd.Title
	}
	if upd.Author != nil {
		newAuthor = *upd.Author
	}

	vec, err := h.embedder.Text(newTitle + " " + newAuthor)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "embedding failed"})
		return
	}

	if err := h.milvus.DeleteByPks(ctx, schema.CollectionBooks, "", entity.NewColumnInt64("id", []int64{id})); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	result, err := h.milvus.Insert(ctx, schema.CollectionBooks, "",
		entity.NewColumnVarChar("isbn", []string{newISBN}),
		entity.NewColumnVarChar("title", []string{newTitle}),
		entity.NewColumnVarChar("author", []string{newAuthor}),
		entity.NewColumnFloatVector("title_vector", schema.VectorDim, [][]float32{vec}),
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"old_id": id, "new_id": result.(*entity.ColumnInt64).Data()[0]})
}

// DELETE /books/:id
func (h *BookHandler) Delete(c *gin.Context) {
	if !checkClient(c, h.milvus) {
		return
	}

	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}

	ctx := safeCtx(c)
	existing, err := h.milvus.QueryByPks(ctx, schema.CollectionBooks, nil,
		entity.NewColumnInt64("id", []int64{id}),
		[]string{"id"},
	)
	if err != nil || len(existing) == 0 || existing[0].Len() == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("book %d not found", id)})
		return
	}

	if err := h.milvus.DeleteByPks(ctx, schema.CollectionBooks, "", entity.NewColumnInt64("id", []int64{id})); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"deleted_id": id})
}

// GET /books/search?query=...&top_k=5
func (h *BookHandler) Search(c *gin.Context) {
	if !checkClient(c, h.milvus) {
		return
	}

	query := c.Query("query")
	if query == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "query param required"})
		return
	}
	topK, _ := strconv.Atoi(c.DefaultQuery("top_k", "5"))

	vec, err := h.embedder.Text(query)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "embedding failed"})
		return
	}

	sp, _ := entity.NewIndexAUTOINDEXSearchParam(1)
	ctx := safeCtx(c)

	// defensive metadata access to avoid nil-pointer in interceptors
	if md, ok := metadata.FromOutgoingContext(ctx); ok {
		_ = md
	}

	results, err := h.milvus.Search(ctx, schema.CollectionBooks, nil,
		"", []string{"id", "isbn", "title", "author"},
		[]entity.Vector{entity.FloatVector(vec)},
		"title_vector",
		entity.COSINE,
		topK,
		sp,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	var books []models.BookOut
	if len(results) > 0 {
		ids := results[0].IDs.(*entity.ColumnInt64).Data()
		scores := results[0].Scores
		isbnCol := results[0].Fields.GetColumn("isbn")
		titleCol := results[0].Fields.GetColumn("title")
		authorCol := results[0].Fields.GetColumn("author")

		for i := range ids {
			isbn, _ := isbnCol.(*entity.ColumnVarChar).ValueByIdx(i)
			title, _ := titleCol.(*entity.ColumnVarChar).ValueByIdx(i)
			author, _ := authorCol.(*entity.ColumnVarChar).ValueByIdx(i)
			books = append(books, models.BookOut{
				ID:     ids[i],
				ISBN:   isbn,
				Title:  title,
				Author: author,
				Score:  scores[i],
			})
		}
	}
	c.JSON(http.StatusOK, books)
}

// ─── helpers ─────────────────────────────────────────────────────────────────

func colsToBooks(cols []entity.Column) []models.BookOut {
	if len(cols) == 0 {
		return nil
	}
	n := cols[0].Len()
	books := make([]models.BookOut, n)

	for _, col := range cols {
		switch col.Name() {
		case "id":
			for i := 0; i < n; i++ {
				books[i].ID, _ = col.(*entity.ColumnInt64).ValueByIdx(i)
			}
		case "isbn":
			for i := 0; i < n; i++ {
				books[i].ISBN, _ = col.(*entity.ColumnVarChar).ValueByIdx(i)
			}
		case "title":
			for i := 0; i < n; i++ {
				books[i].Title, _ = col.(*entity.ColumnVarChar).ValueByIdx(i)
			}
		case "author":
			for i := 0; i < n; i++ {
				books[i].Author, _ = col.(*entity.ColumnVarChar).ValueByIdx(i)
			}
		}
	}
	return books
}

// GET /queries/books/count-by-author?author=George%20Orwell
func (h *BookHandler) CountByAuthor(c *gin.Context) {
	if !checkClient(c, h.milvus) {
		return
	}

	author := c.Query("author")
	if author == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "author query param required"})
		return
	}
	expr := fmt.Sprintf("author == %q", author)
	ctx := safeCtx(c)
	results, err := h.milvus.Query(ctx, schema.CollectionBooks, nil, expr, []string{"id"})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	count := 0
	if len(results) > 0 {
		count = results[0].Len()
	}
	c.JSON(http.StatusOK, gin.H{"author": author, "count": count})
}

// GET /queries/books/search-filtered?query=dystopian&author=George%20Orwell&isbn=978-0-7432-7356-5&top_k=5
// Complex query: vector search + scalar filtering with at least two filter conditions.
func (h *BookHandler) SearchFiltered(c *gin.Context) {
	if !checkClient(c, h.milvus) {
		return
	}

	query := c.Query("query")
	author := c.Query("author")
	isbn := c.Query("isbn")
	if query == "" || author == "" || isbn == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "query, author and isbn query params are required"})
		return
	}
	topK, _ := strconv.Atoi(c.DefaultQuery("top_k", "5"))
	vec, err := h.embedder.Text(query)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "embedding failed"})
		return
	}
	expr := fmt.Sprintf("author == %q && isbn == %q", author, isbn)
	sp, _ := entity.NewIndexAUTOINDEXSearchParam(1)
	ctx := safeCtx(c)
	results, err := h.milvus.Search(ctx, schema.CollectionBooks, nil,
		expr, []string{"id", "isbn", "title", "author"},
		[]entity.Vector{entity.FloatVector(vec)}, "title_vector", entity.COSINE, topK, sp)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, bookSearchResult(results))
}

// GET /queries/books/hybrid?query=dystopian+future&text=war&author=George%20Orwell&top_k=10
//
// True hybrid search: embeds query and text independently into two separate
// vectors, runs two vector searches both filtered by author, then merges
// results keeping the best score per id. isbn is excluded — it is an opaque
// identifier, not a semantic field.
func (h *BookHandler) HybridSearch(c *gin.Context) {
	if !checkClient(c, h.milvus) {
		return
	}

	query := c.Query("query")
	text := c.Query("text")
	author := c.Query("author")
	if query == "" || text == "" || author == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "query, text and author query params are required"})
		return
	}
	topK, _ := strconv.Atoi(c.DefaultQuery("top_k", "10"))

	// Embed query and text independently — two separate vector representations.
	queryVec, err := h.embedder.Text(query)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "embedding failed for query"})
		return
	}
	textVec, err := h.embedder.Text(text)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "embedding failed for text"})
		return
	}

	sp, _ := entity.NewIndexAUTOINDEXSearchParam(1)
	ctx := safeCtx(c)
	outputFields := []string{"id", "isbn", "title", "author"}
	expr := fmt.Sprintf("author == %q", author)

	// First pass: primary query vector filtered by author.
	res1, err := h.milvus.Search(ctx, schema.CollectionBooks, nil,
		expr, outputFields,
		[]entity.Vector{entity.FloatVector(queryVec)},
		"title_vector", entity.COSINE, topK*2, sp)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "primary search failed: " + err.Error()})
		return
	}

	// Second pass: secondary text vector, same author filter.
	res2, err := h.milvus.Search(ctx, schema.CollectionBooks, nil,
		expr, outputFields,
		[]entity.Vector{entity.FloatVector(textVec)},
		"title_vector", entity.COSINE, topK*2, sp)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "secondary search failed: " + err.Error()})
		return
	}

	// Merge: keep highest score per id.
	scoreMap := make(map[int64]models.BookOut)
	for _, res := range [][]client.SearchResult{res1, res2} {
		for _, b := range bookSearchResult(res) {
			if existing, seen := scoreMap[b.ID]; !seen || b.Score > existing.Score {
				scoreMap[b.ID] = b
			}
		}
	}

	// Collect and insertion-sort descending by score, trim to topK.
	merged := make([]models.BookOut, 0, len(scoreMap))
	for _, b := range scoreMap {
		merged = append(merged, b)
	}
	for i := 1; i < len(merged); i++ {
		for j := i; j > 0 && merged[j].Score > merged[j-1].Score; j-- {
			merged[j], merged[j-1] = merged[j-1], merged[j]
		}
	}
	if len(merged) > topK {
		merged = merged[:topK]
	}

	c.JSON(http.StatusOK, merged)
}

// GET /queries/books/search-iterator?query=science+fiction&author=Isaac%20Asimov&batch=50&max=200
//
// Vector search with a scalar filter (author) iterated via offset pagination,
// collecting results in batch-sized pages up to max total. This gives full
// access to the filtered result space without a hard top_k cap.
// isbn is excluded — identifier only.
func (h *BookHandler) SearchWithIterator(c *gin.Context) {
	if !checkClient(c, h.milvus) {
		return
	}

	query := c.Query("query")
	author := c.Query("author")
	if query == "" || author == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "query and author query params are required"})
		return
	}
	batchSize, _ := strconv.Atoi(c.DefaultQuery("batch", "50"))
	maxResults, _ := strconv.Atoi(c.DefaultQuery("max", "200"))
	if batchSize <= 0 {
		batchSize = 50
	}
	if maxResults <= 0 {
		maxResults = 200
	}

	vec, err := h.embedder.Text(query)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "embedding failed"})
		return
	}

	sp, _ := entity.NewIndexAUTOINDEXSearchParam(1)
	ctx := safeCtx(c)
	expr := fmt.Sprintf("author == %q", author)
	outputFields := []string{"id", "isbn", "title", "author"}

	var books []models.BookOut
	for offset := 0; len(books) < maxResults; offset += batchSize {
		remaining := maxResults - len(books)
		fetch := batchSize
		if remaining < fetch {
			fetch = remaining
		}

		results, err := h.milvus.Search(ctx, schema.CollectionBooks, nil,
			expr, outputFields,
			[]entity.Vector{entity.FloatVector(vec)},
			"title_vector", entity.COSINE, fetch, sp,
			client.WithOffset(int64(offset)),
		)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		batch := bookSearchResult(results)
		if len(batch) == 0 {
			break
		}
		books = append(books, batch...)
		if len(batch) < fetch {
			break // exhausted
		}
	}

	c.JSON(http.StatusOK, books)
}

func bookSearchResult(results []client.SearchResult) []models.BookOut {
	var books []models.BookOut
	if len(results) == 0 {
		return books
	}
	ids := results[0].IDs.(*entity.ColumnInt64).Data()
	scores := results[0].Scores
	isbnCol := results[0].Fields.GetColumn("isbn")
	titleCol := results[0].Fields.GetColumn("title")
	authorCol := results[0].Fields.GetColumn("author")
	for i := range ids {
		isbn, _ := isbnCol.(*entity.ColumnVarChar).ValueByIdx(i)
		title, _ := titleCol.(*entity.ColumnVarChar).ValueByIdx(i)
		author, _ := authorCol.(*entity.ColumnVarChar).ValueByIdx(i)
		books = append(books, models.BookOut{ID: ids[i], ISBN: isbn, Title: title, Author: author, Score: scores[i]})
	}
	return books
}
