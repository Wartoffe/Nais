package rs.ac.uns.acs.nais.GraphDatabaseService.service;

import org.springframework.stereotype.Service;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Korisnik;
import rs.ac.uns.acs.nais.GraphDatabaseService.repository.KorisnikRepository;

import java.util.List;

@Service
public class KorisnikService {

    private final KorisnikRepository korisnikRepository;

    public KorisnikService(KorisnikRepository korisnikRepository) {
        this.korisnikRepository = korisnikRepository;
    }

    public List<Korisnik> findAll() {
        return korisnikRepository.findAll();
    }

    public Korisnik findById(String email) {
        return korisnikRepository.findById(email)
                .orElseThrow(() -> new RuntimeException("Korisnik nije pronadjen: " + email));
    }

    public Korisnik create(Korisnik korisnik) {
        return korisnikRepository.save(korisnik);
    }

    public Korisnik azurirajEmail(String emailStari, String emailNovi) {
        return korisnikRepository.azurirajEmail(emailStari, emailNovi);
    }

    public void delete(String email) {
        korisnikRepository.obrisiKorisnika(email);
    }
}
