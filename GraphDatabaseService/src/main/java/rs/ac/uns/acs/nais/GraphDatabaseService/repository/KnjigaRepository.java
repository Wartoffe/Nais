package rs.ac.uns.acs.nais.GraphDatabaseService.repository;

import org.springframework.data.neo4j.repository.Neo4jRepository;
import org.springframework.data.neo4j.repository.query.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import rs.ac.uns.acs.nais.GraphDatabaseService.dto.KorisnikZanrDTO;
import rs.ac.uns.acs.nais.GraphDatabaseService.dto.TopKnjigaDTO;
import rs.ac.uns.acs.nais.GraphDatabaseService.dto.ZanrTrendDTO;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Knjiga;

import java.util.List;

@Repository
public interface KnjigaRepository extends Neo4jRepository<Knjiga, String> {

    // UPIT 1 : Dodaj ili azuriraj zahtev korisnika za knjigu
    // Ako veza postoji, uvecam brojZahteva; ako ne postoji, kreiram je
    @Query("""
        MATCH (u:Korisnik {email: $email})
        MATCH (k:Knjiga {isbn: $isbn})
        MERGE (u)-[r:ZAINTERESOVAN_ZA]->(k)
        ON CREATE SET r.datumZahteva = date(), r.brojZahteva = 1
        ON MATCH SET r.brojZahteva = r.brojZahteva + 1
        RETURN k
        """)
    Knjiga dodajIliAzurirajZahtev(@Param("email") String email, @Param("isbn") String isbn);

    // UPIT 2: Obrisi veze ka trendu ispod praga relevantnosti
    @Query("""
        MATCH (k:Knjiga)-[r:JE_TREND]->(t:Trend)
        WHERE r.relevantnostScore < $prag
        DELETE r
        RETURN count(r)
        """)
    Long obrisiSlabeTrendVeze(@Param("prag") Double prag);

    // UPIT 3 (MATCH+WHERE+WITH+AGG): Preporuka knjiga korisniku na osnovu zanrova koje trazi
    @Query("""
        MATCH (u:Korisnik {email: $email})-[:ZAINTERESOVAN_ZA]->(k:Knjiga)-[:PRIPADA]->(z:Zanr)
        WITH u, z, count(k) AS interesovanje
        ORDER BY interesovanje DESC
        MATCH (z)<-[:PRIPADA]-(preporuka:Knjiga)
        WHERE NOT (u)-[:ZAINTERESOVAN_ZA]->(preporuka)
        WITH preporuka, z.naziv AS zanrIme, interesovanje
        RETURN preporuka, zanrIme, interesovanje
        ORDER BY interesovanje DESC
        LIMIT 10
        """)
    List<Knjiga> preporuciKnjige(@Param("email") String email);

    // UPIT 4 (MATCH+WHERE+WITH+AGG): Top zanrovi po prosecnoj trend relevantnosti
    @Query("""
    MATCH (z:Zanr)<-[:PRIPADA]-(k:Knjiga)-[r:JE_TREND]->(t:Trend)
    WITH z.naziv AS zanrNaziv, t.naziv AS trendIme,
         avg(r.relevantnostScore) AS prosecnaRelevantnost,
         count(k) AS brojKnjiga
    WHERE prosecnaRelevantnost > $minRelevantnost
    RETURN zanrNaziv, trendIme, prosecnaRelevantnost, brojKnjiga
    ORDER BY prosecnaRelevantnost DESC
    """)
    List<ZanrTrendDTO> topZanroviPoTrendu(@Param("minRelevantnost") Double minRelevantnost);

    // UPIT 5 (MATCH+WHERE+WITH+AGG): Korisnici sa najvise zahteva grupisani po zanru
    @Query("""
    MATCH (u:Korisnik)-[r:ZAINTERESOVAN_ZA]->(k:Knjiga)-[:PRIPADA]->(z:Zanr)
    WITH z.naziv AS zanrNaziv, u.ime AS ime, u.prezime AS prezime,
         u.email AS email, sum(r.brojZahteva) AS ukupnoZahteva
    WHERE ukupnoZahteva > 1
    RETURN zanrNaziv, ime, prezime, email, ukupnoZahteva
    ORDER BY zanrNaziv, ukupnoZahteva DESC
    """)
    List<KorisnikZanrDTO> korisniciBrojZahtevaPoZanru();

    //UPIT 6 (NIJE SLOZENI ALI GLAVNA POENTA FUNKCIONALNOSTIIUI!!!): Sistem nalazi najtrazenije knjige i daje predlog za nabavku spram tog trenda.!!!
    @Query("""
        MATCH (k:Korisnik)-[z:ZAINTERESOVAN_ZA]->(knj:Knjiga)
        RETURN knj.isbn AS isbn, knj.naziv AS naziv, knj.autor AS autor,
               SUM(z.brojZahteva) AS ukupnoZahteva
        ORDER BY ukupnoZahteva DESC
        LIMIT 3
    """)
    List<TopKnjigaDTO> nadjiTop3NajtrazenijeKnjige();

}
