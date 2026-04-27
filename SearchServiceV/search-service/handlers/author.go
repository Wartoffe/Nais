package handlers

import (
	"fmt"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/milvus-io/milvus-sdk-go/v2/client"
	"github.com/milvus-io/milvus-sdk-go/v2/entity"

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

// POST /authors
func (h *AuthorHandler) Create(c *gin.Context) {
	var in models.AuthorIn
	if err := c.ShouldBindJSON(&in); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	vec, err := h.embedder.Text(in.Name + " " + in.Lastname)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "embedding failed: " + err.Error()})
		return
	}

	result, err := h.milvus.Insert(nil, schema.CollectionAuthors, "",
		entity.NewColumnVarChar("name", []string{in.Name}),
		entity.NewColumnVarChar("lastname", []string{in.Lastname}),
		entity.NewColumnVarChar("author_id", []string{in.AuthorID}),
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
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))

	results, err := h.milvus.Query(nil, schema.CollectionAuthors, nil,
		"id > 0", []string{"id", "name", "lastname", "author_id"},
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
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}

	results, err := h.milvus.QueryByPks(nil, schema.CollectionAuthors, nil,
		entity.NewColumnInt64("id", []int64{id}),
		[]string{"id", "name", "lastname", "author_id"},
	)
	if err != nil || len(results) == 0 || results[0].Len() == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("author %d not found", id)})
		return
	}

	c.JSON(http.StatusOK, colsToAuthors(results)[0])
}

// PUT /authors/:id
func (h *AuthorHandler) Update(c *gin.Context) {
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

	existing, err := h.milvus.QueryByPks(nil, schema.CollectionAuthors, nil,
		entity.NewColumnInt64("id", []int64{id}),
		[]string{"id", "name", "lastname", "author_id"},
	)
	if err != nil || len(existing) == 0 || existing[0].Len() == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("author %d not found", id)})
		return
	}

	current := colsToAuthors(existing)[0]
	newName := current.Name
	newLast := current.Lastname
	newAID := current.AuthorID
	if upd.Name != nil {
		newName = *upd.Name
	}
	if upd.Lastname != nil {
		newLast = *upd.Lastname
	}
	if upd.AuthorID != nil {
		newAID = *upd.AuthorID
	}

	vec, err := h.embedder.Text(newName + " " + newLast)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "embedding failed"})
		return
	}

	if err := h.milvus.DeleteByPks(nil, schema.CollectionAuthors, "", entity.NewColumnInt64("id", []int64{id})); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	result, err := h.milvus.Insert(nil, schema.CollectionAuthors, "",
		entity.NewColumnVarChar("name", []string{newName}),
		entity.NewColumnVarChar("lastname", []string{newLast}),
		entity.NewColumnVarChar("author_id", []string{newAID}),
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
	id, err := strconv.ParseInt(c.Param("id"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})
		return
	}

	existing, err := h.milvus.QueryByPks(nil, schema.CollectionAuthors, nil,
		entity.NewColumnInt64("id", []int64{id}),
		[]string{"id"},
	)
	if err != nil || len(existing) == 0 || existing[0].Len() == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("author %d not found", id)})
		return
	}

	if err := h.milvus.DeleteByPks(nil, schema.CollectionAuthors, "", entity.NewColumnInt64("id", []int64{id})); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"deleted_id": id})
}

// GET /authors/search?query=...&top_k=5
func (h *AuthorHandler) Search(c *gin.Context) {
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
	results, err := h.milvus.Search(nil, schema.CollectionAuthors, nil,
		"", []string{"id", "name", "lastname", "author_id"},
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

		for i := range ids {
			name, _ := nameCol.(*entity.ColumnVarChar).ValueByIdx(i)
			lastname, _ := lastCol.(*entity.ColumnVarChar).ValueByIdx(i)
			aid, _ := aidCol.(*entity.ColumnVarChar).ValueByIdx(i)
			authors = append(authors, models.AuthorOut{
				ID:       ids[i],
				Name:     name,
				Lastname: lastname,
				AuthorID: aid,
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
		}
	}
	return authors
}

// GET /queries/authors/by-author-id?author_id=AUTH002
func (h *AuthorHandler) ByAuthorID(c *gin.Context) {
	authorID := c.Query("author_id")
	if authorID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "author_id query param required"})
		return
	}
	expr := fmt.Sprintf("author_id == %q", authorID)
	results, err := h.milvus.Query(nil, schema.CollectionAuthors, nil, expr, []string{"id", "name", "lastname", "author_id"}, client.WithLimit(10))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, colsToAuthors(results))
}

// GET /queries/authors/search-filtered?query=orwell&lastname=Orwell&author_id=AUTH002&top_k=5
// Complex query: vector search + scalar filtering with at least two filter conditions.
func (h *AuthorHandler) SearchFiltered(c *gin.Context) {
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
	results, err := h.milvus.Search(nil, schema.CollectionAuthors, nil,
		expr, []string{"id", "name", "lastname", "author_id"},
		[]entity.Vector{entity.FloatVector(vec)}, "bio_vector", entity.COSINE, topK, sp)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, authorSearchResult(results))
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
	for i := range ids {
		name, _ := nameCol.(*entity.ColumnVarChar).ValueByIdx(i)
		lastname, _ := lastCol.(*entity.ColumnVarChar).ValueByIdx(i)
		aid, _ := aidCol.(*entity.ColumnVarChar).ValueByIdx(i)
		authors = append(authors, models.AuthorOut{ID: ids[i], Name: name, Lastname: lastname, AuthorID: aid, Score: scores[i]})
	}
	return authors
}
