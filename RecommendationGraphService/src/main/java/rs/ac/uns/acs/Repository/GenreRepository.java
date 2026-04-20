package rs.ac.uns.acs.Repository;

import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.stereotype.Repository;
import rs.ac.uns.acs.Model.Genre;

@Repository
public interface GenreRepository extends Neo4jRepository<Genre, Long> {
}
