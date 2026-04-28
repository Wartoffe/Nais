package rs.ac.uns.acs.nais.GraphDatabaseService.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import rs.ac.uns.acs.nais.GraphDatabaseService.model.Korisnik;
import rs.ac.uns.acs.nais.GraphDatabaseService.service.KorisnikService;

import java.util.List;

@RestController
@RequestMapping("/api/korisnici")
public class KorisnikController {

    private final KorisnikService korisnikService;

    public KorisnikController(KorisnikService korisnikService) {
        this.korisnikService = korisnikService;
    }

    //CVOR READ
    @GetMapping
    public ResponseEntity<List<Korisnik>> findAll() {
        return ResponseEntity.ok(korisnikService.findAll());
    }

    //CVOR READ
    @GetMapping("/{email}")
    public ResponseEntity<Korisnik> findById(@PathVariable String email) {
        return ResponseEntity.ok(korisnikService.findById(email));
    }

    //CVOR CREATE
    @PostMapping
    public ResponseEntity<Korisnik> create(@RequestBody Korisnik korisnik) {
        return ResponseEntity.ok(korisnikService.create(korisnik));
    }

    //CVOR UPDATE
    @PutMapping("/{email}/email")
    public ResponseEntity<Korisnik> azurirajEmail(
            @PathVariable String email,
            @RequestParam String noviEmail) {
        return ResponseEntity.ok(korisnikService.azurirajEmail(email, noviEmail));
    }

    //CVOR DELETE
    @DeleteMapping("/{email}")
    public ResponseEntity<Void> delete(@PathVariable String email) {
        korisnikService.delete(email);
        return ResponseEntity.noContent().build();
    }
}
