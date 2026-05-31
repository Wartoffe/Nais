package nais.ColumnarDBService.entity;

import org.springframework.data.cassandra.core.cql.Ordering;
import org.springframework.data.cassandra.core.cql.PrimaryKeyType;
import org.springframework.data.cassandra.core.mapping.Column;
import org.springframework.data.cassandra.core.mapping.PrimaryKeyColumn;
import org.springframework.data.cassandra.core.mapping.Table;

import java.util.UUID;

@Table("books_by_genre")
public class BookByGenre {
    @PrimaryKeyColumn(name = "genre", type = PrimaryKeyType.PARTITIONED)
    private String genre;

    @PrimaryKeyColumn(name = "title", ordinal = 0, ordering = Ordering.ASCENDING)
    private String title;

    @PrimaryKeyColumn(name = "book_id", ordinal = 1, ordering = Ordering.ASCENDING)
    private UUID bookId;

    @Column("author")
    private String author;

    @Column("isbn")
    private String isbn;

    @Column("published_year")
    private int publishedYear;

    @Column("total_copies")
    private int totalCopies;

    @Column("available_copies")
    private int availableCopies;

    public BookByGenre() {
    }

    public BookByGenre(String genre, String title, UUID bookId, String author, String isbn, int publishedYear, int totalCopies, int availableCopies) {
        this.genre = genre;
        this.title = title;
        this.bookId = bookId;
        this.author = author;
        this.isbn = isbn;
        this.publishedYear = publishedYear;
        this.totalCopies = totalCopies;
        this.availableCopies = availableCopies;
    }

    public String getGenre() {
        return genre;
    }

    public void setGenre(String genre) {
        this.genre = genre;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public UUID getBookId() {
        return bookId;
    }

    public void setBookId(UUID bookId) {
        this.bookId = bookId;
    }

    public String getAuthor() {
        return author;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public String getIsbn() {
        return isbn;
    }

    public void setIsbn(String isbn) {
        this.isbn = isbn;
    }

    public int getPublishedYear() {
        return publishedYear;
    }

    public void setPublishedYear(int publishedYear) {
        this.publishedYear = publishedYear;
    }

    public int getTotalCopies() {
        return totalCopies;
    }

    public void setTotalCopies(int totalCopies) {
        this.totalCopies = totalCopies;
    }

    public int getAvailableCopies() {
        return availableCopies;
    }

    public void setAvailableCopies(int availableCopies) {
        this.availableCopies = availableCopies;
    }
}
