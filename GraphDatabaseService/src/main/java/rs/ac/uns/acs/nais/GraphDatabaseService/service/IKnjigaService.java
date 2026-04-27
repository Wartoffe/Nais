package rs.ac.uns.acs.nais.GraphDatabaseService.service;

import rs.ac.uns.acs.nais.GraphDatabaseService.model.Knjiga;

import java.util.List;
import java.util.Map;

public interface IKnjigaService {
    List<Knjiga> findAll();
    Knjiga findById(String isbn);
    Knjiga create(Knjiga knjiga);
    Knjiga update(String isbn, Knjiga knjiga);
    void delete(String isbn);

}
