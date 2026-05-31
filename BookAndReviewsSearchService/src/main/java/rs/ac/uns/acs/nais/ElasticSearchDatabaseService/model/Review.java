package rs.ac.uns.acs.nais.ElasticSearchDatabaseService.model;

import lombok.Getter;
import lombok.Setter;
import org.springframework.data.annotation.Id;
import org.springframework.data.elasticsearch.annotations.Document;
import org.springframework.data.elasticsearch.annotations.Field;
import org.springframework.data.elasticsearch.annotations.FieldType;

import java.time.ZonedDateTime;

/**
 * Elasticsearch document model for a book in the "books" index.
 */
@Setter
@Getter
@Document(indexName = "reviews")
public class Review {
    @Id
    private String reviewId;

    @Field(type = FieldType.Keyword)
    private String userId;

    @Field(type = FieldType.Keyword)
    private String bookId;

    @Field(type = FieldType.Integer)
    private Integer rating;

    @Field(type = FieldType.Text, analyzer = "standard")
    private String reviewText;

    @Field(
            type = FieldType.Date,
            format = {},
            pattern = "EEE MMM d HH:mm:ss Z yyyy"
    )
    private ZonedDateTime dateAdded;

    @Field(
            type = FieldType.Date,
            format = {},
            pattern = "EEE MMM d HH:mm:ss Z yyyy"
    )
    private ZonedDateTime dateUpdated;

    @Field(
            type = FieldType.Date,
            format = {},
            pattern = "EEE MMM d HH:mm:ss Z yyyy"
    )
    private ZonedDateTime readAt;

    @Field(
            type = FieldType.Date,
            format = {},
            pattern = "EEE MMM d HH:mm:ss Z yyyy"
    )
    private ZonedDateTime startedAt;

    @Field(type = FieldType.Integer)
    private Integer nVotes;

    @Field(type = FieldType.Integer)
    private Integer nComments;

    public Review(String reviewId, String userId, String bookId, Integer rating, String reviewText, ZonedDateTime dateAdded, ZonedDateTime dateUpdated, ZonedDateTime readAt, ZonedDateTime startedAt, Integer nVotes, Integer nComments) {
        this.reviewId = reviewId;
        this.userId = userId;
        this.bookId = bookId;
        this.rating = rating;
        this.reviewText = reviewText;
        this.dateAdded = dateAdded;
        this.dateUpdated = dateUpdated;
        this.readAt = readAt;
        this.startedAt = startedAt;
        this.nVotes = nVotes;
        this.nComments = nComments;
    }

    public Review() {
    }
}
