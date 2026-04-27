package rs.ac.uns.acs.nais.GraphDatabaseService.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Knjiga;
import rs.ac.uns.acs.nais.GraphDatabaseService.service.IKnjigaService;
import rs.ac.uns.acs.nais.GraphDatabaseService.dto.ZanrTrendDTO;
import rs.ac.uns.acs.nais.GraphDatabaseService.dto.KorisnikZanrDTO;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/knjige")
public class KnjigaController {

    private final IKnjigaService knjigaService;

    public KnjigaController(IKnjigaService knjigaService) {
        this.knjigaService = knjigaService;
    }

    // READ
    @GetMapping
    public ResponseEntity<List<Knjiga>> findAll() {
        return ResponseEntity.ok(knjigaService.findAll());
    }

    // READ
    @GetMapping("/{isbn}")
    public ResponseEntity<Knjiga> findById(@PathVariable String isbn) {
        return ResponseEntity.ok(knjigaService.findById(isbn));
    }

    // CREATE
    @PostMapping
    public ResponseEntity<Knjiga> create(@RequestBody Knjiga knjiga) {
        return ResponseEntity.ok(knjigaService.create(knjiga));
    }

    // UPDATE
    @PutMapping("/{isbn}")
    public ResponseEntity<Knjiga> update(@PathVariable String isbn, @RequestBody Knjiga knjiga) {
        return ResponseEntity.ok(knjigaService.update(isbn, knjiga));
    }

    // DELETE
    @DeleteMapping("/{isbn}")
    public ResponseEntity<Void> delete(@PathVariable String isbn) {
        knjigaService.delete(isbn);
        return ResponseEntity.noContent().build();
    }

    // KOMPLEKSNI UPITI
    // UPIT 1: Dodaj ili azuriraj zahtev korisnika za knjigu
    @PostMapping("/zahtev")
    public ResponseEntity<Knjiga> dodajZahtev(
            @RequestParam String email,
            @RequestParam String isbn) {
        return ResponseEntity.ok(knjigaService.dodajIliAzurirajZahtev(email, isbn));
    }

    // UPIT 2: Obrisi slabe trend veze ispod praga relevantnosti
    @DeleteMapping("/trend-veze")
    public ResponseEntity<Long> obrisiSlabeTrendVeze(@RequestParam Double prag) {
        return ResponseEntity.ok(knjigaService.obrisiSlabeTrendVeze(prag));
    }

    // UPIT 3: Preporuka knjiga korisniku na osnovu zanrova
    @GetMapping("/preporuka/{email}")
    public ResponseEntity<List<Knjiga>> preporuka(@PathVariable String email) {
        return ResponseEntity.ok(knjigaService.preporuciKnjige(email));
    }

    // UPIT 4: Top zanrovi po trendu
    @GetMapping("/top-zanrovi")
    public ResponseEntity<List<ZanrTrendDTO>> topZanrovi(
            @RequestParam(defaultValue = "50.0") Double minRelevantnost) {
        return ResponseEntity.ok(knjigaService.topZanroviPoTrendu(minRelevantnost));
    }

    //UPIT 5: Korisnici sa najvise zahteva grupisani po zanru
    @GetMapping("/zahtevi-po-zanru")
    public ResponseEntity<List<KorisnikZanrDTO>> zahteviPoZanru() {
        return ResponseEntity.ok(knjigaService.korisniciBrojZahtevaPoZanru());
    }


}
