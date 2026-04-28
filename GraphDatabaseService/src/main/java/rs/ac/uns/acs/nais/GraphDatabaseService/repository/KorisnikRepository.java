package rs.ac.uns.acs.nais.GraphDatabaseService.repository;

import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.neo4j.repository.query.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Korisnik;

@Repository
public interface KorisnikRepository extends Neo4jRepository<Korisnik, String> {

    @Query("MATCH (u:Korisnik {email: $emailStari}) SET u.email = $emailNovi RETURN u")
    Korisnik azurirajEmail(@Param("emailStari") String emailStari, @Param("emailNovi") String emailNovi);

    @Query("MATCH (u:Korisnik {email: $email}) DETACH DELETE u")
    void obrisiKorisnika(@Param("email") String email);
}
