package rs.ac.uns.acs.nais.GraphDatabaseService.service;

import org.springframework.stereotype.Service;
import rs.ac.uns.acs.nais.GraphDatabaseService.dto.*;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Knjiga;
import rs.ac.uns.acs.nais.GraphDatabaseService.repository.KnjigaRepository;

import java.util.List;

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


    @Override
    public Knjiga dodajIliAzurirajZahtev(String email, String isbn) {
        return knjigaRepository.dodajIliAzurirajZahtev(email, isbn);
    }

    @Override
    public Long obrisiSlabeTrendVeze(Double prag) {
        return knjigaRepository.obrisiSlabeTrendVeze(prag);
    }

    @Override
    public List<Knjiga> preporuciKnjige(String email) {
        return knjigaRepository.preporuciKnjige(email);
    }

    @Override
    public List<ZanrTrendDTO> topZanroviPoTrendu(Double minRelevantnost) {
        return knjigaRepository.topZanroviPoTrendu(minRelevantnost);
    }

    @Override
    public List<KorisnikZanrDTO> korisniciBrojZahtevaPoZanru() {
        return knjigaRepository.korisniciBrojZahtevaPoZanru();
    }

    public List<TopKnjigaDTO> nadjiTop3Najtrazenije() {
        return knjigaRepository.nadjiTop3NajtrazenijeKnjige();
    }

    public void dodajIliAzurirajJeTrend(String isbn, String naziv, Double score){
        knjigaRepository.dodajIliAzurirajJeTrend(isbn, naziv, score);
    }
    public void obrisiJeTrend(String isbn, String naziv){
        knjigaRepository.obrisiJeTrend(isbn, naziv);
    }
    public List<TrendDTO> nadjiTrendovePoKnjizi(String isbn){
        return knjigaRepository.nadjiTrendovePoKnjizi(isbn);
    }
    public List<KnjigaTrendDTO> nadjiKnjigePoTrendu(String naziv){
        return knjigaRepository.nadjiKnjigePoTrendu(naziv);
    }
    public void setZanrForKnjiga(String isbn, String naziv){
        knjigaRepository.setZanrForKnjiga(isbn, naziv);
    }
    public void removeZanrFromKnjiga(String isbn){
        knjigaRepository.removeZanrFromKnjiga(isbn);
    }
    public ZanrDTO getZanrByKnjiga(String isbn){
        return knjigaRepository.getZanrByKnjiga(isbn);
    }
}
