package rs.ac.uns.acs.Model;

import org.springframework.data.neo4j.core.schema.RelationshipId;
import org.springframework.data.neo4j.core.schema.RelationshipProperties;
import org.springframework.data.neo4j.core.schema.TargetNode;

@RelationshipProperties
public class Similar {

    @RelationshipId
    private Long id;

    @TargetNode
    private Book book;

    private double score;
}
