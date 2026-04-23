package rs.ac.uns.acs.Model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import org.springframework.data.neo4j.core.schema.Id;
import org.springframework.data.neo4j.core.schema.Node;
import org.springframework.data.neo4j.core.schema.Relationship;

import java.util.List;

@Node
public class Book {

    @Id
    private String id;

    private String title;

    @Relationship(type = "BELONGS_TO")
    private Genre genre;

    @JsonIgnore
    @Relationship(type= "SIMILAR_TO")
    private List<Similar> similarBooks;
    @Relationship(type = "WRITTEN_BY")
    private Author author;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public Genre getGenre() {
        return genre;
    }

    public void setGenre(Genre genre) {
        this.genre = genre;
    }

    public List<Similar> getSimilarBooks() {
        return similarBooks;
    }

    public void setSimilarBooks(List<Similar> similarBooks) {
        this.similarBooks = similarBooks;
    }

    public Author getAuthor() {
        return author;
    }

    public void setAuthor(Author author) {
        this.author = author;
    }
}
