package schema

import (
	"context"

	"github.com/milvus-io/milvus-sdk-go/v2/client"
	"github.com/milvus-io/milvus-sdk-go/v2/entity"
)

const (
	ClusterDBName = "library_cluster" 

	CollectionBooks   = "books"
	CollectionAuthors = "authors"
    // nomic-embed-text output dimension
	VectorDim = 768 
)

func BookSchema() *entity.Schema {
	return &entity.Schema{
		CollectionName: CollectionBooks,
		Description:    "Books collection - library cluster",
		AutoID:         true,
		Fields: []*entity.Field{
			{Name: "id", DataType: entity.FieldTypeInt64, PrimaryKey: true, AutoID: true},
			{Name: "isbn", DataType: entity.FieldTypeVarChar, TypeParams: map[string]string{entity.TypeParamMaxLength: "64"}},
			{Name: "title", DataType: entity.FieldTypeVarChar, TypeParams: map[string]string{entity.TypeParamMaxLength: "512"}},
			{Name: "author", DataType: entity.FieldTypeVarChar, TypeParams: map[string]string{entity.TypeParamMaxLength: "256"}},
			{Name: "title_vector", DataType: entity.FieldTypeFloatVector, TypeParams: map[string]string{entity.TypeParamDim: "768"}},
		},
	}
}

func BookIndex() (entity.Index, error) { return entity.NewIndexAUTOINDEX(entity.COSINE) }

func AuthorSchema() *entity.Schema {
	return &entity.Schema{
		CollectionName: CollectionAuthors,
		Description:    "Authors collection - library cluster",
		AutoID:         true,
		Fields: []*entity.Field{
			{Name: "id", DataType: entity.FieldTypeInt64, PrimaryKey: true, AutoID: true},
			{Name: "name", DataType: entity.FieldTypeVarChar, TypeParams: map[string]string{entity.TypeParamMaxLength: "256"}},
			{Name: "lastname", DataType: entity.FieldTypeVarChar, TypeParams: map[string]string{entity.TypeParamMaxLength: "256"}},
			{Name: "author_id", DataType: entity.FieldTypeVarChar, TypeParams: map[string]string{entity.TypeParamMaxLength: "64"}},
			{Name: "country", DataType: entity.FieldTypeVarChar, TypeParams: map[string]string{entity.TypeParamMaxLength: "128"}},
			{Name: "bio_vector", DataType: entity.FieldTypeFloatVector, TypeParams: map[string]string{entity.TypeParamDim: "768"}},
		},
	}
}

func AuthorIndex() (entity.Index, error) { return entity.NewIndexAUTOINDEX(entity.COSINE) }

func EnsureCollections(ctx context.Context, c client.Client) error {
	if err := ensureOne(ctx, c, CollectionBooks, BookSchema(), "title_vector", BookIndex); err != nil {
		return err
	}
	return ensureOne(ctx, c, CollectionAuthors, AuthorSchema(), "bio_vector", AuthorIndex)
}

func ensureOne(ctx context.Context, c client.Client, name string, schema *entity.Schema, vectorField string, idxFn func() (entity.Index, error)) error {
	exists, err := c.HasCollection(ctx, name)
	if err != nil {
		return err
	}
	if !exists {
		if err := c.CreateCollection(ctx, schema, 1); err != nil {
			return err
		}
		idx, err := idxFn()
		if err != nil {
			return err
		}
		if err := c.CreateIndex(ctx, name, vectorField, idx, false); err != nil {
			return err
		}
	}
	return c.LoadCollection(ctx, name, false)
}
