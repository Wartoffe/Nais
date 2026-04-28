package rs.ac.uns.acs.nais.GraphDatabaseService.service;

import org.springframework.data.neo4j.repository.query.Query;
import rs.ac.uns.acs.nais.GraphDatabaseService.dto.*;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Knjiga;

import java.util.List;
import java.util.Map;

public interface IKnjigaService {
    List<Knjiga> findAll();
    Knjiga findById(String isbn);
    Knjiga create(Knjiga knjiga);
    Knjiga update(String isbn, Knjiga knjiga);
    void delete(String isbn);

    Knjiga dodajIliAzurirajZahtev(String email, String isbn);
    Long obrisiSlabeTrendVeze(Double prag);
    List<Knjiga> preporuciKnjige(String email);
    List<ZanrTrendDTO> topZanroviPoTrendu(Double minRelevantnost);
    List<KorisnikZanrDTO> korisniciBrojZahtevaPoZanru();
    List<TopKnjigaDTO> nadjiTop3Najtrazenije();
    void dodajIliAzurirajJeTrend(String isbn, String naziv, Double score);
    void obrisiJeTrend(String isbn, String naziv);
    List<TrendDTO> nadjiTrendovePoKnjizi(String isbn);
    List<KnjigaTrendDTO> nadjiKnjigePoTrendu(String naziv);
    void setZanrForKnjiga(String isbn, String naziv);
    void removeZanrFromKnjiga(String isbn);
    ZanrDTO getZanrByKnjiga(String isbn);
}
