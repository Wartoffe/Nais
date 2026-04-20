package rs.ac.uns.acs.Model;

import org.springframework.data.neo4j.core.schema.Id;
import org.springframework.data.neo4j.core.schema.Node;
import org.springframework.data.neo4j.core.schema.Relationship;

import java.util.List;

@Node
public class Member {

    @Id
    private Long id;

    private String firstName;
    private String lastName;
    private long age;
    @Relationship(type = "BORROWED")
    private List<Borrow> borrowedBooks;

    @Relationship(type = "RECOMMENDED")
    private List<Recommendation> recommendations;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    public long getAge() {
        return age;
    }

    public void setAge(long age) {
        this.age = age;
    }

    public List<Borrow> getBorrowedBooks() {
        return borrowedBooks;
    }

    public void setBorrowedBooks(List<Borrow> borrowedBooks) {
        this.borrowedBooks = borrowedBooks;
    }

    public List<Recommendation> getRecommendations() {
        return recommendations;
    }

    public void setRecommendations(List<Recommendation> recommendations) {
        this.recommendations = recommendations;
    }
}
