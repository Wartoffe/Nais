package rs.ac.uns.acs.nais.GraphDatabaseService.service;

import org.springframework.stereotype.Service;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Zanr;
import rs.ac.uns.acs.nais.GraphDatabaseService.repository.ZanrRepository;

import java.util.List;

@Service
public class ZanrService {

    private final ZanrRepository zanrRepository;

    public ZanrService(ZanrRepository zanrRepository) {
        this.zanrRepository = zanrRepository;
    }

    public List<Zanr> findAll() {
        return zanrRepository.findAll();
    }

    public Zanr findById(String naziv) {
        return zanrRepository.findById(naziv)
                .orElseThrow(() -> new RuntimeException("Zanr nije pronadjen: " + naziv));
    }

    public Zanr create(Zanr zanr) {
        return zanrRepository.save(zanr);
    }

    public Zanr azurirajOpis(String naziv, String noviOpis) {
        return zanrRepository.azurirajOpis(naziv, noviOpis);
    }

    public void delete(String naziv) {
        zanrRepository.obrisiZanr(naziv);
    }
}
