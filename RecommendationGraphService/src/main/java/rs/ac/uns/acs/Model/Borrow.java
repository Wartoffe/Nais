package rs.ac.uns.acs.Model;

import org.springframework.data.neo4j.core.schema.RelationshipId;
import org.springframework.data.neo4j.core.schema.RelationshipProperties;
import org.springframework.data.neo4j.core.schema.TargetNode;

import java.util.Date;

@RelationshipProperties
public class Borrow {
    @RelationshipId
    private Long id;

    @TargetNode
    private Book book;

    private Date date;
}
