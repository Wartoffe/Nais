package rs.ac.uns.acs.nais.GraphDatabaseService.service;

import org.springframework.stereotype.Service;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Knjiga;
import rs.ac.uns.acs.nais.GraphDatabaseService.repository.KnjigaRepository;

import java.util.List;
import java.util.Map;

@Service
public class KnjigaService implements IKnjigaService {

    private final KnjigaRepository knjigaRepository;

    public KnjigaService(KnjigaRepository knjigaRepository) {
        this.knjigaRepository = knjigaRepository;
    }

    @Override
    public List<Knjiga> findAll() {
        return knjigaRepository.findAll();
    }

    @Override
    public Knjiga findById(String isbn) {
        return knjigaRepository.findById(isbn)
                .orElseThrow(() -> new RuntimeException("Knjiga nije pronadjena: " + isbn));
    }

    @Override
    public Knjiga create(Knjiga knjiga) {
        return knjigaRepository.save(knjiga);
    }

    @Override
    public Knjiga update(String isbn, Knjiga knjiga) {
        Knjiga postojeca = findById(isbn);
        postojeca.setNaziv(knjiga.getNaziv());
        postojeca.setAutor(knjiga.getAutor());
        postojeca.setGodinaIzdavanja(knjiga.getGodinaIzdavanja());
        postojeca.setCena(knjiga.getCena());
        return knjigaRepository.save(postojeca);
    }

    @Override
    public void delete(String isbn) {
        knjigaRepository.deleteById(isbn);
    }

}
