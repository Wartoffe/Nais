package rs.ac.uns.acs.Model;

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

    @Relationship(type= "SIMILAR_TO")
    private List<Similar> similarBooks;
}
