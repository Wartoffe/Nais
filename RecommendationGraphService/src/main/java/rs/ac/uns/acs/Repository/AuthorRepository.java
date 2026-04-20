package rs.ac.uns.acs.Repository;

import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.stereotype.Repository;
import rs.ac.uns.acs.Model.Author;

@Repository
public interface AuthorRepository extends Neo4jRepository<Author, Long> {
}
