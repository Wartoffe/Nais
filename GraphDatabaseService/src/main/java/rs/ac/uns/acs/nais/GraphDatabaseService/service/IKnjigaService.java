package rs.ac.uns.acs.nais.GraphDatabaseService.service;

import rs.ac.uns.acs.nais.GraphDatabaseService.dto.KorisnikZanrDTO;
import rs.ac.uns.acs.nais.GraphDatabaseService.dto.ZanrTrendDTO;
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

}
