package rs.ac.uns.acs.nais.GraphDatabaseService.repository;

import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.neo4j.repository.query.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Trend;

@Repository
public interface TrendRepository extends Neo4jRepository<Trend, String> {

    @Query("MATCH (t:Trend {naziv: $naziv}) SET t.score = $score, t.period = $period RETURN t")
    Trend azurirajTrend(@Param("naziv") String naziv, @Param("score") Integer score, @Param("period") String period);

    @Query("MATCH (t:Trend {naziv: $naziv}) DETACH DELETE t")
    void obrisiTrend(@Param("naziv") String naziv);
}
