package rs.ac.uns.acs.nais.GraphDatabaseService.repository;

import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.neo4j.repository.query.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Zanr;

@Repository
public interface ZanrRepository extends Neo4jRepository<Zanr, String> {

    @Query("MATCH (z:Zanr {naziv: $naziv}) SET z.opis = $opis RETURN z")
    Zanr azurirajOpis(@Param("naziv") String naziv, @Param("opis") String opis);

    @Query("MATCH (z:Zanr {naziv: $naziv}) DETACH DELETE z")
    void obrisiZanr(@Param("naziv") String naziv);
}
