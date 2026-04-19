package rs.ac.uns.acs.Repository;

import org.springframework.data.neo4j.repository.Neo4jRepository;
import rs.ac.uns.acs.Model.Genre;

public interface GenreRepository extends Neo4jRepository<Genre, Long> {
}
