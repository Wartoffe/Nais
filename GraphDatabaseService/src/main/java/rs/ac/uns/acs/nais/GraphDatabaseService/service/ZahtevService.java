package rs.ac.uns.acs.nais.GraphDatabaseService.service;

import org.springframework.stereotype.Service;
import rs.ac.uns.acs.nais.GraphDatabaseService.dto.ZahtevDTO;
import rs.ac.uns.acs.nais.GraphDatabaseService.repository.KnjigaRepository;

import java.util.List;

@Service
public class ZahtevService {

    private final KnjigaRepository repo;

    public ZahtevService(KnjigaRepository repo) {
        this.repo = repo;
    }

    public void dodajZahtev(String email, String isbn) {
        repo.dodajIliAzurirajZahtev(email, isbn);
    }

    public void obrisiZahtev(String email, String isbn) {
        repo.obrisiZahtev(email, isbn);
    }

    public List<ZahtevDTO> getZahtevi(String email) {
        return repo.findZahteviByKorisnik(email);
    }
}
