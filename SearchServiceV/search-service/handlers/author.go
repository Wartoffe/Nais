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

type AuthorHandler struct {
	milvus   client.Client
	embedder *embed.Client
}

func NewAuthorHandler(milvus client.Client, embedder *embed.Client) *AuthorHandler {
	return &AuthorHandler{milvus: milvus, embedder: embedder}
}

func safeCtxA(c *gin.Context) context.Context {
	ctx := c.Request.Context()
	if ctx == nil {
		ctx = context.Background()
	}
	return ctx
}

func checkClientA(c *gin.Context, milvus client.Client) bool {
	if milvus == nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "milvus client not initialized"})
		return false
	}
	return true
}

// POST /authors
func (h *AuthorHandler) Create(c *gin.Context) {
	if !checkClientA(c, h.milvus) {
		return
	}

	var in models.AuthorIn
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	ctx := safeCtxA(c)
	existing, err := h.milvus.Query(ctx, schema.CollectionAuthors, nil,
		fmt.Sprintf("author_id == %q", in.AuthorID), []string{"id"}, client.WithLimit(1))
	if err == nil && len(existing) > 0 && existing[0].Len() > 0 {
		c.JSON(http.StatusConflict, gin.H{"error": fmt.Sprintf("author_id %q already exists", in.AuthorID)})
		return
	}

	vec, err := h.embedder.Text(in.Name + " " + in.Lastname + " " + in.Country)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "embedding failed: " + err.Error()})
		return
	}

	result, err := h.milvus.Insert(ctx, schema.CollectionAuthors, "",
		entity.NewColumnVarChar("name", []string{in.Name}),
		entity.NewColumnVarChar("lastname", []string{in.Lastname}),
		entity.NewColumnVarChar("author_id", []string{in.AuthorID}),
		entity.NewColumnVarChar("country", []string{in.Country}),
		entity.NewColumnFloatVector("bio_vector", schema.VectorDim, [][]float32{vec}),
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusCreated, gin.H{"inserted_id": result.(*entity.ColumnInt64).Data()[0]})
}

// GET /authors
func (h *AuthorHandler) List(c *gin.Context) {
	if !checkClientA(c, h.milvus) {
		return
	}

	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))

	ctx := safeCtxA(c)
	results, err := h.milvus.Query(ctx, schema.CollectionAuthors, nil,
		"id > 0", []string{"id", "name", "lastname", "author_id", "country"},
		client.WithLimit(int64(limit)),
		client.WithOffset(int64(offset)),
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, colsToAuthors(results))
}

// GET /authors/:id
func (h *AuthorHandler) Get(c *gin.Context) {
	if !checkClientA(c, h.milvus) {
		return
	}

	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}

	ctx := safeCtxA(c)
	results, err := h.milvus.QueryByPks(ctx, schema.CollectionAuthors, nil,
		entity.NewColumnInt64("id", []int64{id}),
		[]string{"id", "name", "lastname", "author_id", "country"},
	)
	if err != nil || len(results) == 0 || results[0].Len() == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("author %d not found", id)})
		return
	}

	c.JSON(http.StatusOK, colsToAuthors(results)[0])
}

// PUT /authors/:id
func (h *AuthorHandler) Update(c *gin.Context) {
	if !checkClientA(c, h.milvus) {
		return
	}

	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}

	var upd models.AuthorUpdate
	if err := c.ShouldBindJSON(&upd); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	ctx := safeCtxA(c)
	existing, err := h.milvus.QueryByPks(ctx, schema.CollectionAuthors, nil,
		entity.NewColumnInt64("id", []int64{id}),
		[]string{"id", "name", "lastname", "author_id", "country"},
	)
	if err != nil || len(existing) == 0 || existing[0].Len() == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("author %d not found", id)})
		return
	}

	current := colsToAuthors(existing)[0]
	if upd.AuthorID != nil && *upd.AuthorID != current.AuthorID {
		conflict, err := h.milvus.Query(ctx, schema.CollectionAuthors, nil,
			fmt.Sprintf("author_id == %q", *upd.AuthorID), []string{"id"}, client.WithLimit(1))
		if err == nil && len(conflict) > 0 && conflict[0].Len() > 0 {
			c.JSON(http.StatusConflict, gin.H{"error": fmt.Sprintf("author_id %q already exists", *upd.AuthorID)})
			return
		}
	}

	newName := current.Name
	newLast := current.Lastname
	newAID := current.AuthorID
	newCountry := current.Country
	if upd.Name != nil {
		newName = *upd.Name
	}
	if upd.Lastname != nil {
		newLast = *upd.Lastname
	}
	if upd.AuthorID != nil {
		newAID = *upd.AuthorID
	}
	if upd.Country != nil {
		newCountry = *upd.Country
	}

	vec, err := h.embedder.Text(newName + " " + newLast + " " + newCountry)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "embedding failed"})
		return
	}

	if err := h.milvus.DeleteByPks(ctx, schema.CollectionAuthors, "", entity.NewColumnInt64("id", []int64{id})); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	result, err := h.milvus.Insert(ctx, schema.CollectionAuthors, "",
		entity.NewColumnVarChar("name", []string{newName}),
		entity.NewColumnVarChar("lastname", []string{newLast}),
		entity.NewColumnVarChar("author_id", []string{newAID}),
		entity.NewColumnVarChar("country", []string{newCountry}),
		entity.NewColumnFloatVector("bio_vector", schema.VectorDim, [][]float32{vec}),
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"old_id": id, "new_id": result.(*entity.ColumnInt64).Data()[0]})
}

// DELETE /authors/:id
func (h *AuthorHandler) Delete(c *gin.Context) {
	if !checkClientA(c, h.milvus) {
		return
	}

	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}

	ctx := safeCtxA(c)
	existing, err := h.milvus.QueryByPks(ctx, schema.CollectionAuthors, nil,
		entity.NewColumnInt64("id", []int64{id}),
		[]string{"id"},
	)
	if err != nil || len(existing) == 0 || existing[0].Len() == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("author %d not found", id)})
		return
	}

	if err := h.milvus.DeleteByPks(ctx, schema.CollectionAuthors, "", entity.NewColumnInt64("id", []int64{id})); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"deleted_id": id})
}

// GET /authors/search?query=...&top_k=5
func (h *AuthorHandler) Search(c *gin.Context) {
	if !checkClientA(c, h.milvus) {
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
	ctx := safeCtxA(c)

	if md, ok := metadata.FromOutgoingContext(ctx); ok {
		_ = md
	}

	results, err := h.milvus.Search(ctx, schema.CollectionAuthors, nil,
		"", []string{"id", "name", "lastname", "author_id", "country"},
		[]entity.Vector{entity.FloatVector(vec)},
		"bio_vector",
		entity.COSINE,
		topK,
		sp,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	var authors []models.AuthorOut
	if len(results) > 0 {
		ids := results[0].IDs.(*entity.ColumnInt64).Data()
		scores := results[0].Scores
		nameCol := results[0].Fields.GetColumn("name")
		lastCol := results[0].Fields.GetColumn("lastname")
		aidCol := results[0].Fields.GetColumn("author_id")
		countryCol := results[0].Fields.GetColumn("country")

		for i := range ids {
			name, _ := nameCol.(*entity.ColumnVarChar).ValueByIdx(i)
			lastname, _ := lastCol.(*entity.ColumnVarChar).ValueByIdx(i)
			aid, _ := aidCol.(*entity.ColumnVarChar).ValueByIdx(i)
			country, _ := countryCol.(*entity.ColumnVarChar).ValueByIdx(i)
			authors = append(authors, models.AuthorOut{
				ID:       ids[i],
				Name:     name,
				Lastname: lastname,
				AuthorID: aid,
				Country:  country,
				Score:    scores[i],
			})
		}
	}
	c.JSON(http.StatusOK, authors)
}

// ─── helpers ─────────────────────────────────────────────────────────────────

func colsToAuthors(cols []entity.Column) []models.AuthorOut {
	if len(cols) == 0 {
		return nil
	}
	n := cols[0].Len()
	authors := make([]models.AuthorOut, n)

	for _, col := range cols {
		switch col.Name() {
		case "id":
			for i := 0; i < n; i++ {
				authors[i].ID, _ = col.(*entity.ColumnInt64).ValueByIdx(i)
			}
		case "name":
			for i := 0; i < n; i++ {
				authors[i].Name, _ = col.(*entity.ColumnVarChar).ValueByIdx(i)
			}
		case "lastname":
			for i := 0; i < n; i++ {
				authors[i].Lastname, _ = col.(*entity.ColumnVarChar).ValueByIdx(i)
			}
		case "author_id":
			for i := 0; i < n; i++ {
				authors[i].AuthorID, _ = col.(*entity.ColumnVarChar).ValueByIdx(i)
			}
		case "country":
			for i := 0; i < n; i++ {
				authors[i].Country, _ = col.(*entity.ColumnVarChar).ValueByIdx(i)
			}
		}
	}
	return authors
}

// GET /queries/authors/by-author-id?author_id=AUTH002
func (h *AuthorHandler) ByAuthorID(c *gin.Context) {
	if !checkClientA(c, h.milvus) {
		return
	}

	authorID := c.Query("author_id")
	if authorID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "author_id query param required"})
		return
	}
	expr := fmt.Sprintf("author_id == %q", authorID)
	ctx := safeCtxA(c)
	results, err := h.milvus.Query(ctx, schema.CollectionAuthors, nil, expr, []string{"id", "name", "lastname", "author_id", "country"}, client.WithLimit(10))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, colsToAuthors(results))
}

// GET /queries/authors/search-filtered?query=orwell&lastname=Orwell&author_id=AUTH002&top_k=5
// Complex query: vector search + two scalar filters (lastname + author_id).
func (h *AuthorHandler) SearchFiltered(c *gin.Context) {
	if !checkClientA(c, h.milvus) {
		return
	}

	query := c.Query("query")
	lastname := c.Query("lastname")
	authorID := c.Query("author_id")
	if query == "" || lastname == "" || authorID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "query, lastname and author_id query params are required"})
		return
	}
	topK, _ := strconv.Atoi(c.DefaultQuery("top_k", "5"))
	vec, err := h.embedder.Text(query)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "embedding failed"})
		return
	}
	expr := fmt.Sprintf("lastname == %q && author_id == %q", lastname, authorID)
	sp, _ := entity.NewIndexAUTOINDEXSearchParam(1)
	ctx := safeCtxA(c)
	results, err := h.milvus.Search(ctx, schema.CollectionAuthors, nil,
		expr, []string{"id", "name", "lastname", "author_id", "country"},
		[]entity.Vector{entity.FloatVector(vec)}, "bio_vector", entity.COSINE, topK, sp)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, authorSearchResult(results))
}

// GET /queries/authors/search-iterator?query=russian+novelist&lastname=Tolstoy&batch=50&max=200
//
// Complex query: vector search with a scalar filter (lastname) executed via a
// search iterator. author_id is intentionally excluded — it is an opaque
// identifier, not a semantic field. lastname is used as the filter because it
// is a meaningful grouping dimension (e.g. "give me everyone with this
// surname that semantically matches my query").
func (h *AuthorHandler) SearchWithIterator(c *gin.Context) {
	if !checkClientA(c, h.milvus) {
		return
	}

	query := c.Query("query")
	lastname := c.Query("lastname")
	if query == "" || lastname == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "query and lastname query params are required"})
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
	ctx := safeCtxA(c)
	expr := fmt.Sprintf("lastname == %q", lastname)
	outputFields := []string{"id", "name", "lastname", "author_id", "country"}

	var authors []models.AuthorOut
	for offset := 0; len(authors) < maxResults; offset += batchSize {
		remaining := maxResults - len(authors)
		fetch := batchSize
		if remaining < fetch {
			fetch = remaining
		}

		results, err := h.milvus.Search(ctx, schema.CollectionAuthors, nil,
			expr, outputFields,
			[]entity.Vector{entity.FloatVector(vec)},
			"bio_vector", entity.COSINE, fetch, sp,
			client.WithOffset(int64(offset)),
		)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		batch := authorSearchResult(results)
		if len(batch) == 0 {
			break
		}
		authors = append(authors, batch...)
		if len(batch) < fetch {
			break
		}
	}

	c.JSON(http.StatusOK, authors)
}

func authorSearchResult(results []client.SearchResult) []models.AuthorOut {
	var authors []models.AuthorOut
	if len(results) == 0 {
		return authors
	}
	ids := results[0].IDs.(*entity.ColumnInt64).Data()
	scores := results[0].Scores
	nameCol := results[0].Fields.GetColumn("name")
	lastCol := results[0].Fields.GetColumn("lastname")
	aidCol := results[0].Fields.GetColumn("author_id")
	countryCol := results[0].Fields.GetColumn("country")
	for i := range ids {
		name, _ := nameCol.(*entity.ColumnVarChar).ValueByIdx(i)
		lastname, _ := lastCol.(*entity.ColumnVarChar).ValueByIdx(i)
		aid, _ := aidCol.(*entity.ColumnVarChar).ValueByIdx(i)
		country, _ := countryCol.(*entity.ColumnVarChar).ValueByIdx(i)
		authors = append(authors, models.AuthorOut{ID: ids[i], Name: name, Lastname: lastname, AuthorID: aid, Country: country, Score: scores[i]})
	}
	return authors
}
