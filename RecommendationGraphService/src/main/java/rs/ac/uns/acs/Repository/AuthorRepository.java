package rs.ac.uns.acs.Repository;

import org.springframework.data.neo4j.repository.Neo4jRepository;
import rs.ac.uns.acs.Model.Author;

public interface AuthorRepository extends Neo4jRepository<Author, Long> {
}
