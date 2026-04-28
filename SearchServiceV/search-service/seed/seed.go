package seed

import (
	"context"
	"fmt"

	"github.com/milvus-io/milvus-sdk-go/v2/client"
	"github.com/milvus-io/milvus-sdk-go/v2/entity"

	"search-service/embed"
	"search-service/schema"
)

func SeedIfEmpty(ctx context.Context, c client.Client, e *embed.Client) error {
	if err := seedBooks(ctx, c, e); err != nil {
		return err
	}
	return seedAuthors(ctx, c, e)
}

func seedBooks(ctx context.Context, c client.Client, e *embed.Client) error {
	existing, err := c.Query(ctx, schema.CollectionBooks, nil, "id > 0", []string{"id"}, client.WithLimit(1))
	if err == nil && len(existing) > 0 && existing[0].Len() > 0 {
		return nil
	}

	isbns := make([]string, 0, len(Books))
	titles := make([]string, 0, len(Books))
	authors := make([]string, 0, len(Books))
	vectors := make([][]float32, 0, len(Books))

	for _, b := range Books {
		vec, err := e.Text(b[1] + " " + b[2])
		if err != nil {
			return fmt.Errorf("embed book %s: %w", b[1], err)
		}
		isbns = append(isbns, b[0])
		titles = append(titles, b[1])
		authors = append(authors, b[2])
		vectors = append(vectors, vec)
	}

	_, err = c.Insert(ctx, schema.CollectionBooks, "",
		entity.NewColumnVarChar("isbn", isbns),
		entity.NewColumnVarChar("title", titles),
		entity.NewColumnVarChar("author", authors),
		entity.NewColumnFloatVector("title_vector", schema.VectorDim, vectors),
	)
	if err != nil {
		return err
	}
	return c.Flush(ctx, schema.CollectionBooks, false)
}

func seedAuthors(ctx context.Context, c client.Client, e *embed.Client) error {
	existing, err := c.Query(ctx, schema.CollectionAuthors, nil, "id > 0", []string{"id"}, client.WithLimit(1))
	if err == nil && len(existing) > 0 && existing[0].Len() > 0 {
		return nil
	}

	names := make([]string, 0, len(Authors))
	lastnames := make([]string, 0, len(Authors))
	authorIDs := make([]string, 0, len(Authors))
	countries := make([]string, 0, len(Authors))
	vectors := make([][]float32, 0, len(Authors))

	for _, a := range Authors {
		vec, err := e.Text(a[0] + " " + a[1] + " author writer literature " + a[3])
		if err != nil {
			return fmt.Errorf("embed author %s %s: %w", a[0], a[1], err)
		}
		names = append(names, a[0])
		lastnames = append(lastnames, a[1])
		authorIDs = append(authorIDs, a[2])
		countries = append(countries, a[3])
		vectors = append(vectors, vec)
	}

	_, err = c.Insert(ctx, schema.CollectionAuthors, "",
		entity.NewColumnVarChar("name", names),
		entity.NewColumnVarChar("lastname", lastnames),
		entity.NewColumnVarChar("author_id", authorIDs),
		entity.NewColumnVarChar("country", countries),
		entity.NewColumnFloatVector("bio_vector", schema.VectorDim, vectors),
	)
	if err != nil {
		return err
	}
	return c.Flush(ctx, schema.CollectionAuthors, false)
}
