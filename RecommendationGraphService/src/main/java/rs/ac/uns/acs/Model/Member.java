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
}
