package rs.ac.uns.acs.Model;

import org.springframework.data.neo4j.core.schema.Id;
import org.springframework.data.neo4j.core.schema.Node;

@Node
public class Author {
    @Id
    private Long id;

    private String firstName;
    private  String lastName;
}
